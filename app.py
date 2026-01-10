# app.py
# Práctica final visualización de datos (Streamlit)
# Pilar Pérez Hernández - 2ºB iMAT

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.io as pio


# =============================
# 0) Configuración visual general
# =============================

# Fijo la configuración de la página al principio para que Streamlit no muestre avisos
st.set_page_config(page_title="Dashboard Ventas - Práctica Streamlit", layout="wide")

# Mantengo una plantilla clara y consistente en todos los gráficos para una estética más “CEO-friendly”
pio.templates.default = "plotly_white"

st.title("📊 Dashboard de Ventas (Práctica Final)")

# Dejo el sidebar como guía rápida de navegación
st.sidebar.title("📌 Controles")
st.sidebar.write("Uso las pestañas para navegar por el dashboard.")
st.sidebar.markdown(
    "- Pestaña 1: visión global\n"
    "- Pestaña 2: por tienda\n"
    "- Pestaña 3: por estado\n"
    "- Pestaña 4: extra"
)

# Nota de estética (fuera del código):
# Para mejorar mucho el look, conviene crear .streamlit/config.toml con un tema (colores, fondo, fuente).


# =============================
# 1) Carga de datos
# =============================

@st.cache_data(show_spinner=True)
def cargar_datos(ruta_csv: str) -> pd.DataFrame:
    # Cargo el CSV y hago limpiezas mínimas típicas para evitar errores comunes
    df_local = pd.read_csv(ruta_csv, low_memory=False)

    # Elimino columna basura típica si existe
    if "Unnamed: 0" in df_local.columns:
        df_local = df_local.drop(columns=["Unnamed: 0"])

    # Convierto date a datetime si está en el dataset
    if "date" in df_local.columns:
        df_local["date"] = pd.to_datetime(df_local["date"], errors="coerce")

    # Fuerzo tipos numéricos donde suele haber problemas (si existen)
    for col in ["sales", "onpromotion", "transactions", "year", "month", "week"]:
        if col in df_local.columns:
            df_local[col] = pd.to_numeric(df_local[col], errors="coerce")

    return df_local


# Cargo el dataset principal (en Streamlit Cloud tiene que estar en el repo)
df = cargar_datos("parte_1.csv")


# =============================
# 2) Utilidades pequeñas de formato
# =============================

def fmt_int(x) -> str:
    # Formateo enteros con separador de miles estilo ES
    try:
        return f"{int(x):,}".replace(",", ".")
    except Exception:
        return "—"


def fmt_money(x, decimals=2) -> str:
    # Formateo números tipo dinero/ventas estilo ES
    try:
        s = f"{float(x):,.{decimals}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


# =============================
# 3) Agregados Pestaña 1 (en términos medios)
# =============================

@st.cache_data(show_spinner=False)
def agregados_pestana_1(df_in: pd.DataFrame) -> dict:
    # Calculo lo necesario para Pestaña 1 cumpliendo “en términos medios” donde lo pide el enunciado

    # Top 10 productos más vendidos en términos medios -> media de ventas por family
    top_productos = (
        df_in.groupby("family", as_index=False)
             .agg(sales=("sales", "mean"))
             .sort_values("sales", ascending=False)
             .head(10)
    )

    # Distribución de ventas por tienda en términos medios -> media de ventas por store_nbr
    ventas_por_tienda = (
        df_in.groupby("store_nbr", as_index=False)
             .agg(sales=("sales", "mean"))
             .sort_values("sales", ascending=False)
    )

    # Top 10 tiendas con ventas en promoción en términos medios
    df_promo = df_in[df_in["onpromotion"] > 0].copy()
    top_tiendas_promo = (
        df_promo.groupby("store_nbr", as_index=False)
                .agg(sales=("sales", "mean"))
                .sort_values("sales", ascending=False)
                .head(10)
    )

    # Estacionalidad en términos medios
    media_por_dia = (
        df_in.groupby("day_of_week", as_index=False)
             .agg(sales=("sales", "mean"))
             .sort_values("sales", ascending=False)
    )

    media_por_semana = (
        df_in.groupby("week", as_index=False)
             .agg(sales=("sales", "mean"))
             .sort_values("week")
    )

    media_por_mes = (
        df_in.groupby("month", as_index=False)
             .agg(sales=("sales", "mean"))
             .sort_values("month")
    )

    return {
        "top_productos": top_productos,
        "ventas_por_tienda": ventas_por_tienda,
        "top_tiendas_promo": top_tiendas_promo,
        "media_por_dia": media_por_dia,
        "media_por_semana": media_por_semana,
        "media_por_mes": media_por_mes
    }


aggs1 = agregados_pestana_1(df)


# =============================
# 4) Tabs del dashboard
# =============================

tab1, tab2, tab3, tab4 = st.tabs([
    "🌍 Visión global",
    "🏪 Por tienda",
    "🗺️ Por estado",
    "✨ Extra"
])

# =========================================================
# PESTAÑA 1
# =========================================================
with tab1:
    st.subheader("Visión global del dataset")
    st.caption("Resumen global con KPIs, análisis en términos medios y estacionalidad.")

    # KPIs pedidos por el enunciado
    total_tiendas = df["store_nbr"].nunique() if "store_nbr" in df.columns else 0
    total_productos = df["family"].nunique() if "family" in df.columns else 0
    total_estados = df["state"].nunique() if "state" in df.columns else 0

    # “Meses con datos” = número de pares (year, month) distintos
    if "year" in df.columns and "month" in df.columns:
        meses_disponibles = df[["year", "month"]].drop_duplicates().shape[0]
    else:
        meses_disponibles = 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nº total de tiendas", fmt_int(total_tiendas))
    c2.metric("Nº total de productos", fmt_int(total_productos))
    c3.metric("Nº de estados", fmt_int(total_estados))
    c4.metric("Meses con datos", fmt_int(meses_disponibles))

    st.divider()

    st.subheader("Rankings y distribución (en términos medios)")
    st.caption("Uso medias para comparar comportamiento típico (no acumulados).")

    colA, colB = st.columns(2)

    with colA:
        st.markdown("**Top 10 productos más vendidos (ventas medias)**")
        top_prod_plot = aggs1["top_productos"].sort_values("sales")
        fig_top_prod = px.bar(
            top_prod_plot,
            x="sales",
            y="family",
            orientation="h",
            labels={"sales": "Ventas medias", "family": "Familia"}
        )
        fig_top_prod.update_traces(
            hovertemplate="Familia=%{y}<br>Ventas medias=%{x:.2f}<extra></extra>"
        )
        st.plotly_chart(fig_top_prod, use_container_width=True)

    with colB:
        st.markdown("**Distribución de ventas medias por tienda**")
        st.caption("Se muestra cómo se reparte la venta media entre tiendas.")

        fig_dist_tienda = px.histogram(
            aggs1["ventas_por_tienda"],
            x="sales",
            nbins=40,
            labels={"sales": "Ventas medias por tienda"}
        )
        fig_dist_tienda.update_traces(
            hovertemplate="Ventas medias=%{x:.2f}<br>Tiendas=%{y}<extra></extra>"
        )
        st.plotly_chart(fig_dist_tienda, use_container_width=True)

        q10, q50, q90 = aggs1["ventas_por_tienda"]["sales"].quantile([0.10, 0.50, 0.90]).tolist()
        c1, c2, c3 = st.columns(3)
        c1.metric("P10", fmt_money(q10, 2))
        c2.metric("Mediana (P50)", fmt_money(q50, 2))
        c3.metric("P90", fmt_money(q90, 2))

    st.markdown("**Top 10 tiendas con más ventas en promoción (ventas medias en promo)**")
    st.caption("Promoción = onpromotion > 0. Se muestra la venta media en esas observaciones.")

    top_promo_plot = aggs1["top_tiendas_promo"].sort_values("sales")
    fig_top_promo = px.bar(
        top_promo_plot,
        x="sales",
        y="store_nbr",
        orientation="h",
        labels={"sales": "Ventas medias (en promo)", "store_nbr": "Tienda"}
    )
    fig_top_promo.update_traces(
        hovertemplate="Tienda=%{y}<br>Ventas medias (promo)=%{x:.2f}<extra></extra>"
    )
    st.plotly_chart(fig_top_promo, use_container_width=True)

    st.divider()

    st.subheader("Estacionalidad (en términos medios)")
    st.caption("Patrones típicos por día, semana y mes.")

    colC, colD = st.columns(2)

    with colC:
        st.markdown("**Día de la semana con más ventas (media)**")

        orden_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        orden_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

        tmp_dia = aggs1["media_por_dia"].copy()
        dias = tmp_dia["day_of_week"].astype(str).tolist()

        if set(orden_en).issuperset(set(dias)):
            orden = orden_en
        elif set(orden_es).issuperset(set(dias)):
            orden = orden_es
        else:
            orden = sorted(set(dias))

        tmp_dia["day_of_week"] = pd.Categorical(tmp_dia["day_of_week"].astype(str), categories=orden, ordered=True)
        tmp_dia = tmp_dia.sort_values("day_of_week")

        fig_dia = px.bar(
            tmp_dia,
            x="day_of_week",
            y="sales",
            labels={"day_of_week": "Día", "sales": "Ventas medias"}
        )
        st.plotly_chart(fig_dia, use_container_width=True)

    with colD:
        st.markdown("**Ventas medias por semana del año (promedio de todos los años)**")
        fig_sem = px.line(
            aggs1["media_por_semana"],
            x="week",
            y="sales",
            labels={"week": "Semana", "sales": "Ventas medias"}
        )
        st.plotly_chart(fig_sem, use_container_width=True)

    st.markdown("**Ventas medias por mes (promedio de todos los años)**")
    fig_mes = px.line(
        aggs1["media_por_mes"],
        x="month",
        y="sales",
        labels={"month": "Mes", "sales": "Ventas medias"}
    )
    st.plotly_chart(fig_mes, use_container_width=True)

    with st.expander("Ver una muestra del dataset"):
        st.dataframe(df.head(50), use_container_width=True)


# =========================================================
# PESTAÑA 2 (alineada al enunciado)
# =========================================================
with tab2:
    st.subheader("Análisis por tienda")
    st.caption("Selecciono una tienda y muestro: ventas por año y métricas de productos.")

    if "store_nbr" not in df.columns:
        st.error("No existe la columna 'store_nbr' en el dataset.")
    else:
        tiendas = sorted(df["store_nbr"].dropna().unique().tolist())

        # Pongo por defecto la tienda con más ventas totales para que al abrir sea informativo
        ventas_totales_todas = (
            df.groupby("store_nbr", as_index=False)
              .agg(sales=("sales", "sum"))
              .sort_values("sales", ascending=False)
        )
        tienda_top = int(ventas_totales_todas["store_nbr"].iloc[0]) if not ventas_totales_todas.empty else tiendas[0]
        index_default = tiendas.index(tienda_top) if tienda_top in tiendas else 0

        tienda_sel = st.selectbox(
            "Selecciona una tienda (store_nbr):",
            tiendas,
            index=index_default,
            key="tienda_sel"
        )

        df_tienda = df[df["store_nbr"] == tienda_sel].copy()

        st.divider()

        st.markdown("### a) Número total de ventas por año (de más antiguo a más reciente)")
        if "year" not in df_tienda.columns:
            st.warning("No existe la columna 'year' en el dataset.")
        else:
            ventas_por_ano = (
                df_tienda.groupby("year", as_index=False)
                        .agg(sales=("sales", "sum"))
                        .sort_values("year")
            )
            fig_year = px.bar(
                ventas_por_ano,
                x="year",
                y="sales",
                labels={"year": "Año", "sales": "Ventas totales"}
            )
            st.plotly_chart(fig_year, use_container_width=True)

        st.divider()

        # Interpreto “producto” como la categoría family, tal como se usa en el resto del dashboard
        productos_totales = df_tienda["family"].nunique() if "family" in df_tienda.columns else 0

        if "onpromotion" in df_tienda.columns and "family" in df_tienda.columns:
            productos_promo = df_tienda[df_tienda["onpromotion"] > 0]["family"].nunique()
        else:
            productos_promo = 0

        st.markdown("### b) y c) Productos vendidos vs productos en promoción")

        colL, colR = st.columns([1, 2])

        with colL:
            st.metric("Productos vendidos", fmt_int(productos_totales))
            st.metric("Productos en promoción", fmt_int(productos_promo))

        with colR:
            df_comp = pd.DataFrame({
                "Tipo": ["Productos vendidos", "Productos en promoción"],
                "Cantidad": [productos_totales, productos_promo]
            })
            fig_comp = px.bar(df_comp, x="Tipo", y="Cantidad", labels={"Cantidad": "Nº de productos"})
            st.plotly_chart(fig_comp, use_container_width=True)

        with st.expander("Ver muestra de datos de la tienda seleccionada"):
            st.dataframe(df_tienda.head(50), use_container_width=True)


# =========================================================
# PESTAÑA 3 (alineada al enunciado)
# =========================================================
with tab3:
    st.subheader("Análisis por estado")
    st.caption("Selecciono un estado y muestro: transacciones por año, ranking de tiendas y producto líder en una tienda.")

    if "state" not in df.columns:
        st.error("No existe la columna 'state' en el dataset.")
    else:
        estados = sorted(df["state"].dropna().unique().tolist())

        ventas_por_estado = (
            df.groupby("state", as_index=False)
              .agg(sales=("sales", "sum"))
              .sort_values("sales", ascending=False)
        )
        estado_top = str(ventas_por_estado["state"].iloc[0]) if not ventas_por_estado.empty else estados[0]
        index_default = estados.index(estado_top) if estado_top in estados else 0

        estado_sel = st.selectbox(
            "Selecciona un estado (state):",
            estados,
            index=index_default,
            key="estado_sel"
        )

        df_estado = df[df["state"] == estado_sel].copy()

        st.divider()

        st.markdown("### a) Número total de transacciones por año")
        if "transactions" not in df_estado.columns or "year" not in df_estado.columns:
            st.warning("No existe 'transactions' o 'year' en el dataset, así que no puedo graficar transacciones por año.")
        else:
            df_estado["transactions"] = pd.to_numeric(df_estado["transactions"], errors="coerce").fillna(0)
            trans_por_ano = (
                df_estado.groupby("year", as_index=False)
                         .agg(transactions=("transactions", "sum"))
                         .sort_values("year")
            )
            fig_trans = px.bar(
                trans_por_ano,
                x="year",
                y="transactions",
                labels={"year": "Año", "transactions": "Transacciones totales"}
            )
            st.plotly_chart(fig_trans, use_container_width=True)

        st.divider()

        st.markdown("### b) Ranking de tiendas con más ventas (Top 10)")
        if "store_nbr" not in df_estado.columns:
            st.warning("No existe la columna 'store_nbr' en el dataset.")
        else:
            ranking_tiendas = (
                df_estado.groupby("store_nbr", as_index=False)
                         .agg(sales=("sales", "sum"))
                         .sort_values("sales", ascending=False)
                         .head(10)
            )

            total_estado = df_estado["sales"].sum() if "sales" in df_estado.columns else 0
            ranking_tiendas["% ventas estado"] = (
                (ranking_tiendas["sales"] / total_estado) * 100
            ).fillna(0) if total_estado > 0 else 0

            fig_rank = px.bar(
                ranking_tiendas.sort_values("sales"),
                x="sales",
                y="store_nbr",
                orientation="h",
                hover_data={"% ventas estado": ":.2f"},
                labels={"sales": "Ventas totales", "store_nbr": "Tienda"}
            )
            st.plotly_chart(fig_rank, use_container_width=True)

        st.divider()

        st.markdown("### c) Producto más vendido en la tienda")

        # Dentro del estado, tomo la tienda con más ventas y calculo el producto líder (family) en esa tienda
        if "store_nbr" not in df_estado.columns or "family" not in df_estado.columns:
            st.warning("No existe 'store_nbr' o 'family' en el dataset, así que no puedo calcular el producto líder.")
        else:
            ventas_por_tienda_estado = (
                df_estado.groupby("store_nbr", as_index=False)
                         .agg(sales=("sales", "sum"))
                         .sort_values("sales", ascending=False)
            )

            if ventas_por_tienda_estado.empty:
                st.warning("No hay datos suficientes para calcular la tienda y el producto más vendido.")
            else:
                tienda_lider = int(ventas_por_tienda_estado.iloc[0]["store_nbr"])
                df_tienda_lider = df_estado[df_estado["store_nbr"] == tienda_lider].copy()

                top_productos_tienda = (
                    df_tienda_lider.groupby("family", as_index=False)
                                   .agg(sales=("sales", "sum"))
                                   .sort_values("sales", ascending=False)
                                   .head(10)
                )

                producto_lider = top_productos_tienda.iloc[0]["family"]
                st.caption(f"La tienda analizada es la tienda con más ventas dentro del estado: store_nbr = {tienda_lider}.")

                fig_prod_tienda = px.bar(
                    top_productos_tienda.sort_values("sales"),
                    x="sales",
                    y="family",
                    orientation="h",
                    labels={"sales": "Ventas totales", "family": "Familia"}
                )
                st.plotly_chart(fig_prod_tienda, use_container_width=True)

                st.metric("Producto líder (en la tienda líder del estado)", producto_lider)

        with st.expander("Ver muestra de datos del estado seleccionado"):
            st.dataframe(df_estado.head(50), use_container_width=True)


# =========================================================
# PESTAÑA 4 (extra, insights accionables)
# =========================================================
with tab4:
    st.subheader("Extra: insights rápidos para dirección")
    st.caption("Incluyo vistas extra para decisiones rápidas: promociones, uplift, festivos y patrones temporales.")

    # Preparo un indicador de promoción para reutilizarlo en varios análisis
    if "onpromotion" not in df.columns:
        st.warning("No existe la columna 'onpromotion' en el dataset; no se puede analizar promociones.")
    else:
        df_aux = df.copy()
        df_aux["en_promo"] = df_aux["onpromotion"] > 0

        # Elijo año para no mezclar series y mejorar la lectura visual
        anos = sorted(df_aux["year"].dropna().unique().tolist()) if "year" in df_aux.columns else []
        if not anos:
            st.warning("No existe la columna 'year' o no hay años válidos para filtrar.")
        else:
            ano_sel = st.selectbox("Selecciona un año:", anos, index=len(anos) - 1, key="ano_extra")
            df_year = df_aux[df_aux["year"] == ano_sel].copy()

            # -------------------------
            # 1) Impacto de promociones por mes
            # -------------------------
            st.markdown("### 1) Impacto de promociones (por mes)")

            ventas_tot = df_year["sales"].sum() if "sales" in df_year.columns else 0
            ventas_promo = df_year[df_year["en_promo"]]["sales"].sum() if "sales" in df_year.columns else 0
            pct_promo = (ventas_promo / ventas_tot * 100) if ventas_tot > 0 else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Ventas totales (año)", fmt_money(ventas_tot, 2))
            c2.metric("Ventas en promoción (año)", fmt_money(ventas_promo, 2))
            c3.metric("% ventas en promoción", f"{pct_promo:.1f}%")

            promo_mes_year = (
                df_year.groupby(["month", "en_promo"], as_index=False)
                       .agg(sales=("sales", "sum"))
                       .sort_values("month")
            )
            promo_mes_year["Tipo"] = promo_mes_year["en_promo"].map({True: "Con promoción", False: "Sin promoción"})

            fig_promo = px.line(
                promo_mes_year,
                x="month",
                y="sales",
                color="Tipo",
                markers=True,
                labels={"month": "Mes", "sales": "Ventas totales"}
            )
            st.plotly_chart(fig_promo, use_container_width=True)

            # Peso relativo (% promo) por mes para ver dependencia de promociones
            pivot_share = (
                promo_mes_year.pivot_table(index="month", columns="Tipo", values="sales", aggfunc="sum")
                              .fillna(0)
                              .reset_index()
            )
            if "Con promoción" not in pivot_share.columns:
                pivot_share["Con promoción"] = 0
            if "Sin promoción" not in pivot_share.columns:
                pivot_share["Sin promoción"] = 0

            pivot_share["%_promo"] = (
                pivot_share["Con promoción"] / (pivot_share["Con promoción"] + pivot_share["Sin promoción"]) * 100
            ).fillna(0)

            st.markdown("### 1.b) Peso relativo de promociones (% sobre ventas mensuales)")
            fig_share = px.bar(
                pivot_share,
                x="month",
                y="%_promo",
                labels={"month": "Mes", "%_promo": "% ventas en promoción"}
            )
            st.plotly_chart(fig_share, use_container_width=True)

            st.divider()

            # -------------------------
            # 2) Familias donde la promoción tiene más peso
            # -------------------------
            st.markdown("### 2) Familias donde la promoción tiene más peso (Top 10)")

            if "family" in df_year.columns and "sales" in df_year.columns:
                ventas_family = (
                    df_year.groupby("family", as_index=False)
                           .agg(ventas_totales=("sales", "sum"))
                )
                ventas_family_promo = (
                    df_year[df_year["en_promo"]]
                    .groupby("family", as_index=False)
                    .agg(ventas_promo=("sales", "sum"))
                )

                family_merge = ventas_family.merge(ventas_family_promo, on="family", how="left").fillna(0)
                family_merge["%_promo"] = (family_merge["ventas_promo"] / family_merge["ventas_totales"] * 100).fillna(0)

                top_family_promo = family_merge.sort_values("%_promo", ascending=False).head(10)

                fig_family = px.bar(
                    top_family_promo.sort_values("%_promo"),
                    x="%_promo",
                    y="family",
                    orientation="h",
                    labels={"%_promo": "% promo sobre ventas", "family": "Familia"}
                )
                st.plotly_chart(fig_family, use_container_width=True)
            else:
                st.warning("No existe 'family' o 'sales' para construir el ranking de familias.")

            st.divider()

            # -------------------------
            # 3) Efecto de la promoción por familia (uplift)
            # -------------------------
            st.markdown("### 3) Efecto de la promoción por familia (uplift)")

            # Uplift = (venta media con promo / venta media sin promo) - 1
            # No demuestra causalidad, pero aporta una señal rápida para dirección.
            if "family" in df_year.columns and "sales" in df_year.columns:
                df_p = df_year[df_year["en_promo"]].copy()
                df_np = df_year[~df_year["en_promo"]].copy()

                mean_p = df_p.groupby("family", as_index=False).agg(mean_sales_promo=("sales", "mean"))
                mean_np = df_np.groupby("family", as_index=False).agg(mean_sales_no_promo=("sales", "mean"))

                uplift = mean_np.merge(mean_p, on="family", how="outer").fillna(0)
                uplift["uplift"] = 0.0

                mask = uplift["mean_sales_no_promo"] > 0
                uplift.loc[mask, "uplift"] = uplift.loc[mask, "mean_sales_promo"] / uplift.loc[mask, "mean_sales_no_promo"] - 1

                top_uplift = uplift.sort_values("uplift", ascending=False).head(10)

                fig_uplift = px.bar(
                    top_uplift.sort_values("uplift"),
                    x="uplift",
                    y="family",
                    orientation="h",
                    labels={"uplift": "Uplift (promo vs no promo)", "family": "Familia"}
                )
                fig_uplift.update_traces(
                    hovertemplate="Familia=%{y}<br>Uplift=%{x:.2%}<extra></extra>"
                )
                st.plotly_chart(fig_uplift, use_container_width=True)
            else:
                st.warning("No existe 'family' o 'sales' para calcular uplift.")

            st.divider()

            # -------------------------
            # 4) Festivos y ventas
            # -------------------------
            st.markdown("### 4) Festivos y ventas (comparativa rápida)")

            # Considero “día festivo” cuando holiday_type no es nulo y no es vacío
            if "holiday_type" in df_year.columns and "sales" in df_year.columns:
                df_h = df_year.copy()
                df_h["es_festivo"] = df_h["holiday_type"].notna() & (df_h["holiday_type"].astype(str).str.strip() != "")

                ventas_festivo = df_h[df_h["es_festivo"]]["sales"].mean() if df_h["es_festivo"].any() else 0
                ventas_no_festivo = df_h[~df_h["es_festivo"]]["sales"].mean() if (~df_h["es_festivo"]).any() else 0

                c1, c2 = st.columns(2)
                c1.metric("Venta media en días festivos", fmt_money(ventas_festivo, 2))
                c2.metric("Venta media en días no festivos", fmt_money(ventas_no_festivo, 2))

                top_holiday = (
                    df_h[df_h["es_festivo"]]
                    .groupby("holiday_type", as_index=False)
                    .agg(sales_mean=("sales", "mean"))
                    .sort_values("sales_mean", ascending=False)
                    .head(10)
                )

                if not top_holiday.empty:
                    fig_holiday = px.bar(
                        top_holiday.sort_values("sales_mean"),
                        x="sales_mean",
                        y="holiday_type",
                        orientation="h",
                        labels={"sales_mean": "Venta media", "holiday_type": "Tipo de festivo"}
                    )
                    st.plotly_chart(fig_holiday, use_container_width=True)
                else:
                    st.info("En el año seleccionado no hay suficientes registros marcados como festivo para rankear por tipo.")
            else:
                st.warning("No existe 'holiday_type' o 'sales' para analizar festivos.")

            st.divider()

            # -------------------------
            # 5) Heatmap Mes vs Día semana
            # -------------------------
            st.markdown("### 5) Heatmap de patrón temporal (Mes vs Día de la semana)")

            if "month" not in df_year.columns or "day_of_week" not in df_year.columns or "sales" not in df_year.columns:
                st.warning("Faltan columnas ('month', 'day_of_week', 'sales') para construir el heatmap.")
            else:
                metrica = st.radio(
                    "Métrica para el heatmap:",
                    ["Media de ventas", "Ventas totales"],
                    horizontal=True,
                    key="metrica_heatmap"
                )

                if metrica == "Media de ventas":
                    heat = df_year.groupby(["month", "day_of_week"], as_index=False).agg(sales=("sales", "mean"))
                else:
                    heat = df_year.groupby(["month", "day_of_week"], as_index=False).agg(sales=("sales", "sum"))

                orden_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                orden_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

                dias = heat["day_of_week"].astype(str).unique().tolist()
                if set(orden_en).issuperset(set(dias)):
                    orden = orden_en
                elif set(orden_es).issuperset(set(dias)):
                    orden = orden_es
                else:
                    orden = sorted(set(dias))

                heat["day_of_week"] = pd.Categorical(heat["day_of_week"].astype(str), categories=orden, ordered=True)
                heat = heat.sort_values(["month", "day_of_week"])

                pivot = heat.pivot(index="day_of_week", columns="month", values="sales")
                fig_heat = px.imshow(
                    pivot,
                    aspect="auto",
                    labels={"x": "Mes", "y": "Día de la semana", "color": "Ventas"}
                )
                st.plotly_chart(fig_heat, use_container_width=True)

    st.info("Esta pestaña extra está pensada para sacar conclusiones accionables (promos, uplift, festivos y estacionalidad).")
