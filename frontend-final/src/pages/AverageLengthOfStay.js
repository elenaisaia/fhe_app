
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

const ageGroups = [
  {
    key: 'under 18',
    label: 'Under 18',
    color: '#0ea5e9',
  },
  {
    key: '18 to 65',
    label: '18-65',
    color: '#6366f1',
  },
  {
    key: 'over 65',
    label: 'Over 65',
    color: '#f43f5e',
  },
];

const tooltipSorter = (item) =>
    ageGroups.findIndex((g) => g.key === item.dataKey);

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
        {ageGroups.map((group) => (
            <li
                key={group.key}
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
                backgroundColor: group.color,
                display: 'inline-block',
                borderRadius: 2,
              }}
          />

              <span style={{ color: '#475569' }}>
            {group.label}
          </span>
            </li>
        ))}
      </ul>
  );
}

function AverageLengthOfStay() {
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
            'http://127.0.0.1:8000/hospitalizations/generate-average-length-of-stay',
            {
              method: 'GET',
            }
        );

        const result = await response.json();

        if (!response.ok) {
          throw new Error(
              result.message ||
              'Failed to load average length of stay.'
          );
        }

        setRawData(result);

        const yearlyData = Object.entries(result).map(
            ([year, values]) => ({
              year,
              'under 18': values.general?.['under 18'] ?? 0,
              '18 to 65': values.general?.['18 to 65'] ?? 0,
              'over 65': values.general?.['over 65'] ?? 0,
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
            'under 18': values['under 18'] ?? 0,
            '18 to 65': values['18 to 65'] ?? 0,
            'over 65': values['over 65'] ?? 0,
          }))
      : [];

  if (loading) {
    return (
        <MetricPage
            title="Average length of stay"
            icon="bi-clock-history"
            color="#0d6efd"
            description="Track how long patients stay in the hospital on average across departments."
            generateEndpoint={STATISTICS_ENDPOINTS.averageLengthOfStay}
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
            title="Average length of stay"
            icon="bi-clock-history"
            color="#0d6efd"
            description="Track how long patients stay in the hospital on average across departments."
            generateEndpoint={STATISTICS_ENDPOINTS.averageLengthOfStay}
        >
          <Alert variant="danger">
            {error}
          </Alert>
        </MetricPage>
    );
  }

  const tooltipFormatter = (value, name) => [
    `${value} days`,
    ageGroups.find((g) => g.key === name)?.label || name,
  ];


  return (
    <MetricPage
      title="Average length of stay"
      icon="bi-clock-history"
      color="#0d6efd"
      description="Track how long patients stay in the hospital on average across departments."
      generateEndpoint={STATISTICS_ENDPOINTS.averageLengthOfStay}
    >
      <h5 className="fw-semibold text-center mb-1">
        Average length of stay by year and age group
      </h5>
      <p className="text-center text-muted small mb-4">
        Tip: click a year to see its monthly breakdown. 2026 figures are year-to-date.
      </p>
      <ResponsiveContainer width="100%" height={420}>
        <BarChart
          data={data}
          margin={{ top: 10, right: 20, left: 0, bottom: 20 }}
          onClick={handleBarClick}
          style={{ cursor: 'pointer' }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="year" tick={{ fill: '#475569' }} />
          <YAxis
            tick={{ fill: '#475569' }}
            label={{
              value: 'Average length of stay (days)',
              angle: -90,
              position: 'insideLeft',
              style: { textAnchor: 'middle', fill: '#475569' },
            }}
          />
          <Tooltip itemSorter={tooltipSorter} formatter={tooltipFormatter} />
          <Legend content={<OrderedLegend />} />
          {ageGroups.map((group) => (
            <Bar key={group.key} dataKey={group.key} fill={group.color} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>

      {selectedYear && (
        <div className="mt-5 pt-4 border-top">
          <h5 className="fw-semibold text-center mb-4">
            Monthly average length of stay in {selectedYear}
          </h5>
          <ResponsiveContainer width="100%" height={420}>
            <BarChart data={monthlyData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tick={{ fill: '#475569' }} />
              <YAxis
                tick={{ fill: '#475569' }}
                label={{
                  value: 'Average length of stay (days)',
                  angle: -90,
                  position: 'insideLeft',
                  style: { textAnchor: 'middle', fill: '#475569' },
                }}
              />
              <Tooltip itemSorter={tooltipSorter} formatter={(value) => [`${value} days`, '']} />
              <Legend content={<OrderedLegend />} />
              {ageGroups.map((group) => (
                <Bar key={group.key} dataKey={group.key} fill={group.color} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-5 pt-4 border-top">
        <h5 className="fw-semibold text-center mb-4">
          Average length of stay by year and age group (trend)
        </h5>
        <ResponsiveContainer width="100%" height={420}>
          <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="year" tick={{ fill: '#475569' }} />
            <YAxis
              tick={{ fill: '#475569' }}
              label={{
                value: 'Average length of stay (days)',
                angle: -90,
                position: 'insideLeft',
                style: { textAnchor: 'middle', fill: '#475569' },
              }}
            />
            <Tooltip itemSorter={tooltipSorter} formatter={(value) => [`${value} days`, '']} />
            <Legend content={<OrderedLegend />} />
            {ageGroups.map((group) => (
              <Line
                key={group.key}
                type="monotone"
                dataKey={group.key}
                stroke={group.color}
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

export default AverageLengthOfStay;

