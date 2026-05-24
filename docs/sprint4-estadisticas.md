# Dashboard de Estadísticas — Documentación técnica

## Arquitectura general

El flujo de datos es unidireccional:

```
SQLite DB → SQLAlchemy (conexión) → Pandas (procesamiento) → FastAPI (endpoint JSON) → React + Recharts (visualización)
```

---

## Backend

### Pandas

Librería de análisis de datos de Python. La razón de usarla en lugar de hacer las
agregaciones directamente con SQLAlchemy es que Pandas ofrece operaciones vectorizadas
sobre DataFrames (tablas en memoria) que son más expresivas para estadísticas:

```python
# En vez de escribir SQL con GROUP BY y COUNT...
det_counts = (
    detections_df.groupby("mission_id")
    .size()
    .reset_index(name="count")
)
# ...o iterar filas manualmente con Python
```

`pd.read_sql(query, connection)` lee el resultado de una query SQL directamente
en un DataFrame. Requiere una conexión activa — por eso se usa
`with engine.connect() as conn:` en lugar de pasar el engine directamente
(cambio de API en SQLAlchemy 2.x).

---

### SQLAlchemy 2.x y el `engine`

El `engine` es el objeto central de conexión a la DB. En SQLAlchemy 2.0 se abandonó
la API legacy de pasar el engine directo a pandas:

```python
# SQLAlchemy 1.x (ya no funciona bien)
pd.read_sql("SELECT ...", engine)

# SQLAlchemy 2.x (correcto)
with engine.connect() as conn:
    pd.read_sql("SELECT ...", conn)
```

El `with` garantiza que la conexión se cierra al terminar, aunque haya un error.

---

### Procesamiento de cada gráfico

#### 1. Detecciones por misión

```python
detections_df.groupby("mission_id").size()
```

`groupby` agrupa filas por `mission_id`, `size()` cuenta cuántas hay en cada grupo.
El resultado se hace `merge` con la tabla de misiones para traer el nombre.
Las misiones sin nombre tienen `NaN` en pandas (no `None`), por eso el chequeo usa `pd.notna()`:

```python
def label(row):
    return row["name"] if pd.notna(row["name"]) and row["name"] else f"Misión #{row['id']}"
```

#### 2. Distribución de confianza y fuente de detección

```python
detections_df["confidence"].value_counts()  # {"high": 450, "medium": 300, "low": 109}
detections_df["source"].value_counts()      # {"rgb": 500, "thermal": 200, "fusion": 159}
```

`value_counts()` cuenta ocurrencias únicas de cada valor en una columna.
Es equivalente a `SELECT confidence, COUNT(*) FROM detections GROUP BY confidence`.

#### 3. Detecciones en el tiempo

```python
detections_df["date"] = pd.to_datetime(detections_df["timestamp"]).dt.date
timeline = (
    detections_df.groupby("date")
    .size()
    .reset_index(name="count")
    .sort_values("date")
)
timeline["date"] = timeline["date"].astype(str)  # para que sea JSON serializable
```

`pd.to_datetime()` parsea el string ISO del campo `timestamp` a un objeto datetime.
`.dt.date` extrae solo la fecha (sin hora). Después se agrupa por fecha y se cuenta.

---

### FastAPI y serialización

El endpoint devuelve un dict Python con listas de dicts. FastAPI lo serializa a JSON
automáticamente. El problema que apareció durante el desarrollo: `NaN` de pandas
**no es JSON válido** (JSON no tiene NaN, solo `null`). Si algún campo era `NaN`,
la serialización lanzaba:

```
ValueError: Out of range float values are not JSON compliant: nan
```

Por eso el chequeo con `pd.notna()` en la función `label` era crítico.

---

## Frontend

### Recharts

Librería de gráficos para React construida sobre D3.js, pero con API declarativa
de componentes. Cada gráfico es un árbol de componentes React:

```tsx
<ResponsiveContainer width="100%" height={260}>  {/* hace el gráfico responsive */}
  <BarChart data={[...]}>                         {/* tipo de gráfico + datos */}
    <XAxis dataKey="label" />                     {/* eje X, qué campo usar */}
    <YAxis />                                     {/* eje Y */}
    <Tooltip />                                   {/* tooltip al hover */}
    <Bar dataKey="count">                         {/* qué columna graficar */}
      <Cell fill="#29B6F6" />                     {/* color de cada barra */}
    </Bar>
  </BarChart>
</ResponsiveContainer>
```

`ResponsiveContainer` usa un `ResizeObserver` internamente para adaptar el gráfico
al tamaño del contenedor padre. Sin él, habría que definir width/height fijos en píxeles.

---

### Los cinco gráficos implementados

| Componente Recharts | Tipo visual | Dato visualizado |
|---|---|---|
| `BarChart` | Barras verticales | Detecciones por misión |
| `PieChart` con `innerRadius` | Donut | Distribución de confianza |
| `PieChart` con `innerRadius` | Donut | Fuente de detección (RGB / Thermal / Fusion) |
| `BarChart` | Barras verticales | Cobertura de grilla por misión (%) |
| `AreaChart` | Área con línea | Detecciones acumuladas en el tiempo |

#### PieChart como donut

Al definir `innerRadius={50}` y `outerRadius={90}`, el pie chart se convierte en donut.
Sin `innerRadius` es un gráfico de torta sólido.

#### AreaChart con gradiente SVG

```tsx
<defs>
  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="5%"  stopColor="#29B6F6" stopOpacity={0.3} />
    <stop offset="95%" stopColor="#29B6F6" stopOpacity={0}   />
  </linearGradient>
</defs>
<Area fill="url(#areaGrad)" />
```

El gradiente va de 30% opaco arriba a transparente abajo, dando el efecto de área
que se desvanece hacia el eje X.

---

### Tipado con TypeScript

La interface `OverviewData` define exactamente qué forma tiene el JSON del backend,
lo que da autocompletado y previene errores de typo en los `dataKey` de Recharts:

```typescript
interface OverviewData {
  detections_per_mission:  { id: number; label: string; count: number }[]
  confidence_distribution: { name: string; value: number }[]
  source_distribution:     { name: string; value: number }[]
  coverage_per_mission:    { id: number; label: string; coverage_percent: number }[]
  detections_timeline:     { date: string; count: number }[]
}
```

---

### Gestión de estado y ciclo de vida

```typescript
const [data, setData]       = useState<OverviewData | null>(null)
const [loading, setLoading] = useState(true)
const [error, setError]     = useState<string | null>(null)

useEffect(() => {
  fetch('http://localhost:8000/api/stats/overview')
    .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
    .then(setData)
    .catch(e => setError(e.message))
    .finally(() => setLoading(false))
}, [])
```

El `useEffect` con dependencias vacías `[]` corre solo al montar el componente (una vez).
El `finally` asegura que `loading` se desactiva siempre, tanto en éxito como en error.
El componente renderiza tres estados: cargando, error, o los gráficos.

---

### Layout con CSS Grid

```typescript
const gridStyle = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',  // dos columnas de igual ancho
  gap: 20,
}
```

Las cards que ocupan todo el ancho usan `gridColumn: '1 / -1'`
(desde la columna 1 hasta la última). El `AreaChart` de detecciones en el tiempo
está en esa posición para darle más espacio horizontal al eje de fechas.
