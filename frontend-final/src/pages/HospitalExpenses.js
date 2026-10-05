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
  { key: 'personnel', label: 'Personnel', color: '#0ea5e9' },
  { key: 'supplies', label: 'Supplies', color: '#6366f1' },
  { key: 'medicine', label: 'Medicine', color: '#f43f5e' },
  { key: 'equipment', label: 'Equipment', color: '#22c55e' },
  { key: 'renovations', label: 'Renovations', color: '#f59e0b' },
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

const formatMillions = (value) =>
    `€${(Number(value) / 1000000).toLocaleString('de-DE', {
      maximumFractionDigits: 1,
    })}M`;

const formatTooltip = (value, name) => [
  `€${Number(value).toLocaleString('de-DE')}`,
  categories.find((c) => c.key === name)?.label || name,
];

function HospitalExpenses() {
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
            'http://127.0.0.1:8000/expenses/generate-hospital-expenses',
            {
              method: 'GET',
            }
        );

        const result = await response.json();

        if (!response.ok) {
          throw new Error(
              result.message || 'Failed to load hospital expenses.'
          );
        }

        setRawData(result);

        const yearlyData = Object.entries(result).map(
            ([year, values]) => ({
              year,
              personnel: values.general?.personnel ?? 0,
              supplies: values.general?.supplies ?? 0,
              medicine: values.general?.medicine ?? 0,
              equipment: values.general?.equipment ?? 0,
              renovations: values.general?.renovations ?? 0,
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
            personnel: values.personnel ?? 0,
            supplies: values.supplies ?? 0,
            medicine: values.medicine ?? 0,
            equipment: values.equipment ?? 0,
            renovations: values.renovations ?? 0,
          }))
      : [];

  if (loading) {
    return (
        <MetricPage
            title="Hospital expenses"
            icon="bi-bar-chart-line"
            color="#fd7e14"
            description="Monitor the hospital's overall operational and financial expenses."
            generateEndpoint={STATISTICS_ENDPOINTS.hospitalExpenses}
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
            title="Hospital expenses"
            icon="bi-bar-chart-line"
            color="#fd7e14"
            description="Monitor the hospital's overall operational and financial expenses."
            generateEndpoint={STATISTICS_ENDPOINTS.hospitalExpenses}
        >
          <Alert variant="danger">
            {error}
          </Alert>
        </MetricPage>
    );
  }


  return (
    <MetricPage
      title="Hospital expenses"
      icon="bi-bar-chart-line"
      color="#fd7e14"
      description="Monitor the hospital's overall operational and financial expenses."
      generateEndpoint={STATISTICS_ENDPOINTS.hospitalExpenses}
    >
      <h5 className="fw-semibold text-center mb-1">
        Hospital expenses by year and category
      </h5>
      <p className="text-center text-muted small mb-4">
        Tip: click a year to see its monthly breakdown. 2026 figures are year-to-date.
      </p>
      <ResponsiveContainer width="100%" height={420}>
        <BarChart data={data} margin={{ top: 10, right: 20, left: 20, bottom: 20 }} onClick={handleBarClick} style={{ cursor: 'pointer' }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="year" tick={{ fill: '#475569' }} />
          <YAxis
            tick={{ fill: '#475569' }}
            tickFormatter={formatMillions}
            label={{
              value: 'Hospital expenses (€)',
              angle: -90,
              position: 'insideLeft',
              style: { textAnchor: 'middle', fill: '#475569' },
            }}
          />
          <Tooltip itemSorter={tooltipSorter} formatter={formatTooltip} />
          <Legend content={<OrderedLegend />} />
          {categories.map((category) => (
            <Bar key={category.key} dataKey={category.key} fill={category.color} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>

      {selectedYear && (
        <div className="mt-5 pt-4 border-top">
          <h5 className="fw-semibold text-center mb-4">
            Monthly hospital expenses in {selectedYear}
          </h5>
          <ResponsiveContainer width="100%" height={420}>
            <BarChart data={monthlyData} margin={{ top: 10, right: 20, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tick={{ fill: '#475569' }} />
              <YAxis
                tick={{ fill: '#475569' }}
                tickFormatter={formatMillions}
                label={{
                  value: 'Hospital expenses (€)',
                  angle: -90,
                  position: 'insideLeft',
                  style: { textAnchor: 'middle', fill: '#475569' },
                }}
              />
              <Tooltip itemSorter={tooltipSorter} formatter={formatTooltip} />
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
          Hospital expenses by year and category (trend)
        </h5>
        <ResponsiveContainer width="100%" height={420}>
          <LineChart data={data} margin={{ top: 10, right: 20, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="year" tick={{ fill: '#475569' }} />
            <YAxis
              tick={{ fill: '#475569' }}
              tickFormatter={formatMillions}
              label={{
                value: 'Hospital expenses (€)',
                angle: -90,
                position: 'insideLeft',
                style: { textAnchor: 'middle', fill: '#475569' },
              }}
            />
            <Tooltip itemSorter={tooltipSorter} formatter={formatTooltip} />
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

export default HospitalExpenses;

