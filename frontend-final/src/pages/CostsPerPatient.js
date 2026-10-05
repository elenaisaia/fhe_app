
import { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Alert, Spinner } from 'react-bootstrap';
import MetricPage from './MetricPage';
import { STATISTICS_ENDPOINTS } from '../api/statistics';

const categories = [
  {
    key: 'services',
    label: 'Medical services',
    color: '#0ea5e9',
  },
  {
    key: 'hospitalization',
    label: 'Hospitalization',
    color: '#6366f1',
  },
  {
    key: 'meds',
    label: 'Meds',
    color: '#f43f5e',
  },
  {
    key: 'meals',
    label: 'Meals',
    color: '#22c55e',
  },
];

const tooltipSorter = (item) =>
    categories.findIndex((c) => c.key === item.dataKey);

function OrderedLegend() {
  return (
      <ul
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '1.5rem',
            listStyle: 'none',
            padding: 0,
            margin: '0.75rem 0 0',
            flexWrap: 'wrap',
          }}
      >
        {categories.map((category) => (
            <li
                key={category.key}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                }}
            >
          <span
              style={{
                width: 12,
                height: 12,
                backgroundColor: category.color,
                display: 'inline-block',
                borderRadius: 2,
              }}
          />

              <span style={{ color: '#475569' }}>
            {category.label}
          </span>
            </li>
        ))}
      </ul>
  );
}

function CostsPerPatient() {
  const [selectedYear, setSelectedYear] = useState(null);

  const [data, setData] = useState([]);
  const [rawData, setRawData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);

        const response = await fetch(
            'http://127.0.0.1:8000/hospitalizations/generate-costs-per-patient',
            {
              method: 'GET',
            }
        );

        const result = await response.json();

        if (!response.ok) {
          throw new Error(
              result.message ||
              'Failed to load costs per patient.'
          );
        }

        setRawData(result);

        const yearlyData = Object.entries(result).map(
            ([year, values]) => ({
              year,
              services: values.general?.services ?? 0,
              hospitalization:
                  values.general?.hospitalization ?? 0,
              meds: values.general?.meds ?? 0,
              meals: values.general?.meals ?? 0,
            })
        );

        yearlyData.sort(
            (a, b) => Number(a.year) - Number(b.year)
        );

        setData(yearlyData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleBarClick = (payload) => {
    const year = payload && payload.activeLabel;

    if (!year) {
      return;
    }

    setSelectedYear((current) =>
        current === year ? null : year
    );
  };

  const monthlyData = selectedYear
      ? Object.entries(rawData[selectedYear] || {})
          .filter(([month]) => month !== 'general')
          .map(([month, values]) => ({
            month,
            services: values.services ?? 0,
            hospitalization:
                values.hospitalization ?? 0,
            meds: values.meds ?? 0,
            meals: values.meals ?? 0,
          }))
      : [];

  if (loading) {
    return (
        <MetricPage
            title="Costs per patient"
            icon="bi-cash-stack"
            color="#198754"
            description="Analyze the average treatment and care cost for each patient."
            generateEndpoint={STATISTICS_ENDPOINTS.costsPerPatient}
        >
          <div className="text-center py-5">
            <Spinner animation="border" />
          </div>
        </MetricPage>
    );
  }

  if (error) {
    return (
        <MetricPage
            title="Costs per patient"
            icon="bi-cash-stack"
            color="#198754"
            description="Analyze the average treatment and care cost for each patient."
            generateEndpoint={STATISTICS_ENDPOINTS.costsPerPatient}
        >
          <Alert variant="danger">
            {error}
          </Alert>
        </MetricPage>
    );
  }

  const formatCost = (value, name) => [
    `€${Number(value).toLocaleString('de-DE')}`,
    categories.find((c) => c.key === name)?.label || name,
  ];


  return (
    <MetricPage
      title="Costs per patient"
      icon="bi-cash-stack"
      color="#198754"
      description="Analyze the average treatment and care cost for each patient."
      generateEndpoint={STATISTICS_ENDPOINTS.costsPerPatient}
    >
      <h5 className="fw-semibold text-center mb-1">
        Cost per patient by year and category
      </h5>
      <p className="text-center text-muted small mb-4">
        Tip: click a year to see its monthly breakdown. 2026 figures are year-to-date.
      </p>
      <ResponsiveContainer width="100%" height={420}>
        <BarChart
          data={data}
          margin={{ top: 10, right: 20, left: 10, bottom: 20 }}
          onClick={handleBarClick}
          style={{ cursor: 'pointer' }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="year" tick={{ fill: '#475569' }} />
          <YAxis
            tick={{ fill: '#475569' }}
            label={{
              value: 'Cost per patient (€)',
              angle: -90,
              position: 'insideLeft',
              style: { textAnchor: 'middle', fill: '#475569' },
            }}
          />
          <Tooltip itemSorter={tooltipSorter} formatter={formatCost} />
          <Legend content={<OrderedLegend />} />
          {categories.map((category) => (
            <Bar key={category.key} dataKey={category.key} fill={category.color} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>

      {selectedYear && (
        <div className="mt-5 pt-4 border-top">
          <h5 className="fw-semibold text-center mb-4">
            Monthly cost per patient in {selectedYear}
          </h5>
          <ResponsiveContainer width="100%" height={420}>
            <BarChart data={monthlyData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tick={{ fill: '#475569' }} />
              <YAxis
                tick={{ fill: '#475569' }}
                label={{
                  value: 'Cost per patient (€)',
                  angle: -90,
                  position: 'insideLeft',
                  style: { textAnchor: 'middle', fill: '#475569' },
                }}
              />
              <Tooltip itemSorter={tooltipSorter} formatter={formatCost} />
              <Legend content={<OrderedLegend />} />
              {categories.map((category) => (
                <Bar key={category.key} dataKey={category.key} fill={category.color} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-5 pt-4 border-top">
        <h5 className="fw-semibold text-center mb-4">
          Cost per patient by year and category (trend)
        </h5>
        <ResponsiveContainer width="100%" height={420}>
          <LineChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="year" tick={{ fill: '#475569' }} />
            <YAxis
              tick={{ fill: '#475569' }}
              label={{
                value: 'Cost per patient (€)',
                angle: -90,
                position: 'insideLeft',
                style: { textAnchor: 'middle', fill: '#475569' },
              }}
            />
            <Tooltip itemSorter={tooltipSorter} formatter={formatCost} />
            <Legend content={<OrderedLegend />} />
            {categories.map((category) => (
              <Line
                key={category.key}
                type="linear"
                dataKey={category.key}
                stroke={category.color}
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </MetricPage>
  );
}

export default CostsPerPatient;

