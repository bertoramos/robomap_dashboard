
import numpy as np
import plotly.graph_objects as go
from scipy.ndimage import gaussian_filter
from scipy.interpolate import griddata
from PIL import Image
import base64
from io import BytesIO

def toImgCoord(x, y, width=100, height=100, margin_x=0, margin_y=0):
    x = np.asarray(x)
    y = np.asarray(y)
    
    xrange = (x.min(), x.max())
    yrange = (y.min(), y.max())

    x_den = xrange[1] - xrange[0]
    y_den = yrange[1] - yrange[0]

    x_norm = np.zeros_like(x, dtype=float)
    y_norm = np.zeros_like(y, dtype=float)

    if x_den != 0:
        x_norm = (x - xrange[0]) / x_den
    if y_den != 0:
        y_norm = (y - yrange[0]) / y_den

    draw_width = max(width - 2 * margin_x, 1)
    draw_height = max(height - 2 * margin_y, 1)

    x_px = (margin_x + x_norm * draw_width).astype(int)
    y_px = (margin_y + y_norm * draw_height).astype(int)

    return x_px, y_px

def create_heatmap(points, background_image=None, width=900, height=600):
    # ========================================
    # Imagen de fondo opcional
    # ========================================
    img_base64 = None
    if background_image is not None:
        img = Image.open(background_image)
        width, height = img.size

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
    
    # ========================================
    # Convertir coordenadas a px imagen
    # ========================================
    x = points[:, 0]
    y = points[:, 1]
    rssi = points[:, 2]

    margin_x = 20
    margin_y = 20
    x_px, y_px = toImgCoord(x, y, height=height, width=width, margin_x=margin_x, margin_y=margin_y)

    # ========================================
    # Interpolacion + suavizado gaussiano
    # ========================================
    resolution = 300  # resolucion del grid

    xi = np.linspace(0, width, resolution)
    yi = np.linspace(0, height, resolution)
    xi_grid, yi_grid = np.meshgrid(xi, yi)

    # Rango RSSI fijo para colores y normalizacion
    # zmin, zmax = -80.0, 0.0
    zmin, zmax = rssi.min(), rssi.max()
    if zmin == zmax:
        tickvals = [int(np.round(zmin))]
    else:
        ticks = np.linspace(zmin, zmax, num=5)
        tickvals = sorted(set(int(np.round(v)) for v in ticks))
    ticktext = [str(v) for v in tickvals]

    # Interpolar valores en todo el grid
    interp_method = "cubic" if len(x_px) >= 4 else ("linear" if len(x_px) >= 3 else "nearest")
    try:
        zi = griddata((x_px, y_px), rssi, (xi_grid, yi_grid), method=interp_method, fill_value=zmin)
    except Exception as e:
        # fallback to nearest if even linear fails
        zi = griddata((x_px, y_px), rssi, (xi_grid, yi_grid), method="nearest", fill_value=zmin)

    # Aplicar suavizado gaussiano (sigma alto = mas difuminado, estilo eye-tracking)
    sigma = 10  # Ajusta: mas alto -> mas suave y difuminado
    zi_smooth = gaussian_filter(zi, sigma=sigma)

    # Normalizar para mascara de transparencia
    zrange = zmax - zmin
    if zrange == 0:
        zi_norm = np.ones_like(zi_smooth)
    else:
        zi_norm = (zi_smooth - zmin) / zrange
    zi_norm = np.clip(zi_norm, 0, 1)

    # ========================================
    # Crear mascara de transparencia (ocultar zonas sin datos)
    # ========================================
    # Las zonas con valor muy bajo se hacen transparentes
    threshold_norm = 0.05
    zi_display = np.where(zi_norm > threshold_norm, zi_smooth, np.nan)

    # Texto de hover con control de NaN
    hover_text = np.empty_like(zi_display, dtype=object)
    mask = np.isnan(zi_display)
    hover_text[mask] = "RSSI: sin datos"
    hover_text[~mask] = np.array([f"RSSI: {v:.1f} dBm" for v in zi_display[~mask]])

    # ========================================
    # Colorscale personalizada estilo eye-tracking
    # ========================================
    colorscale_eyetracking = [
        [0.0, "rgba(0, 128, 0, 0.0)"],      # Transparente
        [0.15, "rgba(0, 128, 0, 0.3)"],      # Verde suave
        [0.3, "rgba(0, 200, 0, 0.5)"],       # Verde
        [0.45, "rgba(144, 238, 0, 0.6)"],    # Verde-amarillo
        [0.6, "rgba(255, 255, 0, 0.7)"],     # Amarillo
        [0.75, "rgba(255, 165, 0, 0.8)"],    # Naranja
        [0.9, "rgba(255, 69, 0, 0.85)"],     # Rojo-naranja
        [1.0, "rgba(255, 0, 0, 0.9)"],       # Rojo intenso
    ]
    
    # ========================================
    # Crear figura
    # ========================================

    fig = go.Figure()

    # Imagen de fondo (plano)
    if img_base64 is not None:
        fig.add_layout_image(
            dict(
                source=img_base64,
                x=0, y=0,
                sizex=width, sizey=height,
                xref="x", yref="y",
                sizing="stretch",
                layer="below",
                opacity=1.0,
            )
        )

    # Heatmap suavizado estilo eye-tracking
    # Interpolar x, y, rssi al grid para hover
    from scipy.interpolate import griddata as gd
    grid_x = gd((x_px, y_px), x, (xi_grid, yi_grid), method=interp_method, fill_value=np.nan)
    grid_y = gd((x_px, y_px), y, (xi_grid, yi_grid), method=interp_method, fill_value=np.nan)
    grid_rssi = gd((x_px, y_px), rssi, (xi_grid, yi_grid), method=interp_method, fill_value=np.nan)
    grid_customdata = np.dstack([grid_x, grid_y, grid_rssi])

    fig.add_trace(go.Heatmap(
        x=xi,
        y=yi,
        z=zi_display,
        text=hover_text,
        colorscale=colorscale_eyetracking,
        zmin=zmin, zmax=zmax,
        opacity=1.0,
        showscale=True,
        colorbar=dict(
            title=dict(text="RSSI (dBm)", side="right"),
            thickness=15,
            len=0.6,
            tickvals=tickvals,
            ticktext=ticktext,
            x=1.02,
            xanchor="left",
            y=0.5,
        ),
        customdata=grid_customdata,
        hovertemplate=(
            "X: %{customdata[0]:.2f}<br>"
            "Y: %{customdata[1]:.2f}<br>"
            "RSSI: %{customdata[2]:.1f} dBm<extra></extra>"
        ),
        connectgaps=False,
    ))

    # Puntos de medicion (pintados en px, mostrando coordenada real)
    customdata = np.column_stack([x, y, rssi])
    fig.add_trace(go.Scatter(
        x=x_px, y=y_px,
        mode="markers+text",
        marker=dict(
            size=12,
            color="white",
            symbol="circle",
            line=dict(width=2, color="black"),
        ),
        text=[f"{v:.2f} dBm" for v in rssi],
        textposition="top center",
        textfont=dict(size=10, color="black"),
        name="Puntos de medicion",
        customdata=customdata,
        hovertemplate=(
            "Punto de medicion<br>"
            "X: %{customdata[0]:.2f}<br>"
            "Y: %{customdata[1]:.2f}<br>"
            "RSSI: %{customdata[2]:.1f} dBm<extra></extra>"
        ),
    ))

    # ── Ejes con unidades reales (metros) ──────────────────────────
    x_min, x_max = float(x.min()), float(x.max())
    y_min, y_max = float(y.min()), float(y.max())

    def _nice_ticks(vmin, vmax, n=6):
        """Return ~n nicely-spaced tick values between vmin and vmax."""
        rng = vmax - vmin
        if rng == 0:
            return [vmin]
        raw_step = rng / max(n - 1, 1)
        mag = 10 ** np.floor(np.log10(raw_step))
        nice = [1, 2, 2.5, 5, 10]
        step = min(nice, key=lambda s: abs(s * mag - raw_step)) * mag
        start = np.ceil(vmin / step) * step
        ticks = []
        v = start
        while v <= vmax + step * 0.01:
            ticks.append(round(v, 10))
            v += step
        return ticks

    x_range_real = (x_max - x_min) if (x_max - x_min) != 0 else 1.0
    y_range_real = (y_max - y_min) if (y_max - y_min) != 0 else 1.0

    # scaleratio para que 1 metro en X se vea igual que 1 metro en Y
    # El eje X cubre 'width' unidades para x_range_real metros
    # El eje Y cubre 'height' unidades para y_range_real metros
    # scaleratio = (height * x_range_real) / (width * y_range_real)
    scaleratio = (height * x_range_real) / (width * y_range_real)

    x_ticks_m = _nice_ticks(x_min, x_max)
    y_ticks_m = _nice_ticks(y_min, y_max)

    x_ticks_px, _ = toImgCoord(
        np.array(x_ticks_m), np.zeros(len(x_ticks_m)),
        width=width, height=height, margin_x=margin_x, margin_y=margin_y,
    )
    # use original x for normalization range
    x_ticks_px, _ = toImgCoord(
        np.array(x_ticks_m), np.full(len(x_ticks_m), y_min),
        width=width, height=height, margin_x=margin_x, margin_y=margin_y,
    )
    # recompute properly using same min/max as the data
    def _real_to_px(vals, vmin, vmax, size, margin):
        vals = np.asarray(vals, dtype=float)
        denom = vmax - vmin
        if denom == 0:
            return np.full_like(vals, margin, dtype=int)
        normed = (vals - vmin) / denom
        draw = max(size - 2 * margin, 1)
        return (margin + normed * draw).astype(int)

    x_tickvals = _real_to_px(x_ticks_m, x_min, x_max, width, margin_x).tolist()
    y_tickvals = _real_to_px(y_ticks_m, y_min, y_max, height, margin_y).tolist()
    x_ticktext = [f"{v:.2g}" for v in x_ticks_m]
    y_ticktext = [f"{v:.2g}" for v in y_ticks_m]

    # Dimensiones de la figura proporcionales al rango real en metros
    # Se fija el lado mayor a 800px y el menor se calcula con el ratio real
    MAX_PX = 800
    MARGIN_EXTRA = 160  # márgenes (l+r o t+b)
    if y_range_real >= x_range_real:
        fig_height = MAX_PX + MARGIN_EXTRA
        fig_width  = int(MAX_PX * (x_range_real / y_range_real)) + MARGIN_EXTRA
    else:
        fig_width  = MAX_PX + MARGIN_EXTRA
        fig_height = int(MAX_PX * (y_range_real / x_range_real)) + MARGIN_EXTRA

    fig.update_layout(
        title=dict(text=""),
        xaxis=dict(
            range=[0, width],
            visible=True,
            title=dict(text="X (m)"),
            tickvals=x_tickvals,
            ticktext=x_ticktext,
            scaleanchor="y",
            scaleratio=scaleratio,
            constrain="domain",
            domain=[0, 1],
            showgrid=False,
        ),
        yaxis=dict(
            range=[0, height],  # Y crece hacia arriba
            visible=True,
            title=dict(text="Y (m)"),
            tickvals=y_tickvals,
            ticktext=y_ticktext,
            constrain="domain",
            domain=[0, 1],
            showgrid=False,
        ),
        width=fig_width,
        height=fig_height,
        margin=dict(l=60, r=20, t=10, b=80),
        plot_bgcolor="white",
        # Botones interactivos
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.0, y=1.1,
                pad=dict(t=10),
                bgcolor="#2d6cdf",
                bordercolor="#1f4fbf",
                font=dict(color="#000000"),
                buttons=[
                    dict(
                        label="Mostrar puntos",
                        method="update",
                        args=[{"visible": [True, True]}],
                    ),
                    dict(
                        label="Solo heatmap",
                        method="update",
                        args=[{"visible": [True, False]}],
                    ),
                ],
            )
        ],
        # Slider para opacidad
        sliders=[
            dict(
                active=10,
                currentvalue=dict(prefix="Opacidad: ", suffix=""),
                pad=dict(t=40, b=0),
                x=0.05, y=-0.15,
                steps=[
                    dict(
                        method="restyle",
                        args=["opacity", [o / 10]],
                        label=f"{o / 10:.1f}",
                    )
                    for o in range(0, 11)
                ],
            )
        ],
    )

    return fig
