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
  { key: 'icu', label: 'ICU', color: '#dc2626' },
  { key: 'er', label: 'ER', color: '#2563eb' },
  { key: 'surgery', label: 'Surgery', color: '#7c3aed' },
  { key: 'hospitalization', label: 'Hospitalization', color: '#059669' },
];

const ageGroups = [
  { key: 'under 18', label: 'Under 18', color: '#38bdf8' },
  { key: '18 to 65', label: '18-65', color: '#6366f1' },
  { key: 'over 65', label: 'Over 65', color: '#f43f5e' },
];

const dk = (category, ageGroup) => `${category}__${ageGroup}`;

const label = (category, ageGroup) => {
  const categoryLabel =
      categories.find((c) => c.key === category)?.label || category;

  const ageLabel =
      ageGroups.find((g) => g.key === ageGroup)?.label || ageGroup;

  return `${categoryLabel} · ${ageLabel}`;
};

const barOrder = [];

categories.forEach((category) => {
  ageGroups.forEach((ageGroup) => {
    barOrder.push(dk(category.key, ageGroup.key));
  });
});

const tooltipSorter = (item) => {
  const index = barOrder.indexOf(item.dataKey);

  if (index !== -1) {
    return index;
  }

  return categories.findIndex(
      (category) => category.key === item.dataKey
  );
};

const legendStyle = {
  display: 'flex',
  justifyContent: 'center',
  gap: '1.5rem',
  listStyle: 'none',
  padding: 0,
  margin: '0.75rem 0 0',
  flexWrap: 'wrap',
};

const legendItemStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.4rem',
};

const swatchStyle = {
  width: 12,
  height: 12,
  display: 'inline-block',
  borderRadius: 2,
};

function AgeGroupLegend() {
  return (
      <ul style={legendStyle}>
        {ageGroups.map((group) => (
            <li
                key={group.key}
                style={legendItemStyle}
            >
          <span
              style={{
                ...swatchStyle,
                backgroundColor: group.color,
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

function CategoryLegend() {
  return (
      <ul style={legendStyle}>
        {categories.map((category) => (
            <li
                key={category.key}
                style={legendItemStyle}
            >
          <span
              style={{
                ...swatchStyle,
                backgroundColor: category.color,
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

function MortalityRate() {
  const [selectedYear, setSelectedYear] = useState(null);

  const [data, setData] = useState([]);
  const [rawData, setRawData] = useState({});
  const [trendData, setTrendData] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);

        const response = await fetch(
            'http://127.0.0.1:8000/hospitalizations/generate-mortality-rate',
            {
              method: 'GET',
            }
        );

        const result = await response.json();

        if (!response.ok) {
          throw new Error(
              result.message ||
              'Failed to load mortality rate.'
          );
        }

        setRawData(result);

        const yearlyData = Object.entries(result).map(
            ([year, values]) => {
              const row = {
                year,
              };

              categories.forEach((category) => {
                ageGroups.forEach((ageGroup) => {
                  row[
                      dk(category.key, ageGroup.key)
                      ] =
                      values.general?.[category.key]?.[
                          ageGroup.key
                          ] ?? 0;
                });
              });

              return row;
            }
        );

        yearlyData.sort(
            (a, b) => Number(a.year) - Number(b.year)
        );

        setData(yearlyData);

        const trend = yearlyData.map((row) => {
          const trendRow = {
            year: row.year,
          };

          categories.forEach((category) => {
            const total = ageGroups.reduce(
                (sum, ageGroup) =>
                    sum +
                    (row[
                        dk(
                            category.key,
                            ageGroup.key
                        )
                        ] || 0),
                0
            );

            trendRow[category.key] =
                Math.round(total * 100) / 100;
          });

          return trendRow;
        });

        setTrendData(trend);
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
          .map(([month, values]) => {
            const row = {
              month,
            };

            categories.forEach((category) => {
              ageGroups.forEach((ageGroup) => {
                row[
                    dk(category.key, ageGroup.key)
                    ] =
                    values?.[category.key]?.[
                        ageGroup.key
                        ] ?? 0;
              });
            });

            return row;
          })
      : [];

  if (loading) {
    return (
        <MetricPage
            title="Mortality rate"
            icon="bi-heart-pulse"
            color="#dc3545"
            description="Review patient mortality rates and trends over time."
            generateEndpoint={STATISTICS_ENDPOINTS.mortalityRate}
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
            title="Mortality rate"
            icon="bi-heart-pulse"
            color="#dc3545"
            description="Review patient mortality rates and trends over time."
            generateEndpoint={STATISTICS_ENDPOINTS.mortalityRate}
        >
          <Alert variant="danger">
            {error}
          </Alert>
        </MetricPage>
    );
  }

  const formatPercent = (value, name) => [
    `${Number(value).toFixed(2)}%`,
    name,
  ];

  const renderStackedBars = () =>
      categories.map((category) =>
          ageGroups.map((ageGroup) => (
              <Bar
                  key={`${category.key}-${ageGroup.key}`}
                  dataKey={dk(
                      category.key,
                      ageGroup.key
                  )}
                  stackId={category.key}
                  fill={ageGroup.color}
                  name={label(
                      category.key,
                      ageGroup.key
                  )}
              />
          ))
      );


  return (
    <MetricPage
      title="Mortality rate"
      icon="bi-heart-pulse"
      color="#dc3545"
      description="Review patient mortality rates and trends over time."
      generateEndpoint={STATISTICS_ENDPOINTS.mortalityRate}
    >
      <h5 className="fw-semibold text-center mb-1">
        Mortality rate by year and department
      </h5>
      <p className="text-center text-muted small mb-4">
        Each year shows 4 stacked bars (left&rarr;right): ICU, ER, Surgery, Hospitalization — split
        by age group. Click a year to see its monthly breakdown. 2026 figures are year-to-date.
      </p>
      <ResponsiveContainer width="100%" height={440}>
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
            tickFormatter={(v) => `${v}%`}
            label={{
              value: 'Mortality rate (%)',
              angle: -90,
              position: 'insideLeft',
              style: { textAnchor: 'middle', fill: '#475569' },
            }}
          />
          <Tooltip itemSorter={tooltipSorter} formatter={formatPercent} />
          <Legend content={<AgeGroupLegend />} />
          {renderStackedBars()}
        </BarChart>
      </ResponsiveContainer>

      {selectedYear && (
        <div className="mt-5 pt-4 border-top">
          <h5 className="fw-semibold text-center mb-4">
            Monthly mortality rate in {selectedYear}
          </h5>
          <ResponsiveContainer width="100%" height={440}>
            <BarChart data={monthlyData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tick={{ fill: '#475569' }} />
              <YAxis
                tick={{ fill: '#475569' }}
                tickFormatter={(v) => `${v}%`}
                label={{
                  value: 'Mortality rate (%)',
                  angle: -90,
                  position: 'insideLeft',
                  style: { textAnchor: 'middle', fill: '#475569' },
                }}
              />
              <Tooltip itemSorter={tooltipSorter} formatter={formatPercent} />
              <Legend content={<AgeGroupLegend />} />
              {renderStackedBars()}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-5 pt-4 border-top">
        <h5 className="fw-semibold text-center mb-4">
          Overall mortality rate by department (trend)
        </h5>
        <ResponsiveContainer width="100%" height={420}>
          <LineChart data={trendData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="year" tick={{ fill: '#475569' }} />
            <YAxis
              tick={{ fill: '#475569' }}
              tickFormatter={(v) => `${v}%`}
              label={{
                value: 'Mortality rate (%)',
                angle: -90,
                position: 'insideLeft',
                style: { textAnchor: 'middle', fill: '#475569' },
              }}
            />
            <Tooltip itemSorter={tooltipSorter} formatter={formatPercent} />
            <Legend content={<CategoryLegend />} />
            {categories.map((c) => (
              <Line
                key={c.key}
                type="linear"
                dataKey={c.key}
                name={c.key}
                stroke={c.color}
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

export default MortalityRate;

