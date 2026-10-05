import { useNavigate } from 'react-router-dom';
import { Container, Row, Col, Card, Button, Navbar } from 'react-bootstrap';

const metrics = [
  {
    title: 'Average length of stay',
    icon: 'bi-clock-history',
    color: '#0d6efd',
    path: '/average-length-of-stay',
  },
  {
    title: 'Costs per patient',
    icon: 'bi-cash-stack',
    color: '#198754',
    path: '/costs-per-patient',
  },
  {
    title: 'Hospital expenses',
    icon: 'bi-bar-chart-line',
    color: '#fd7e14',
    path: '/hospital-expenses',
  },
  {
    title: 'Mortality rate',
    icon: 'bi-heart-pulse',
    color: '#dc3545',
    path: '/mortality-rate',
  },
];

function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="dashboard-page d-flex flex-column min-vh-100">
      <Navbar className="app-navbar shadow-sm px-3">
        <Navbar.Brand className="d-flex align-items-center gap-2 fw-bold">
          <i className="bi bi-activity"></i>
          MedIntel
        </Navbar.Brand>
        <div className="ms-auto">
          <Button variant="light" size="sm" onClick={() => navigate('/')}>
            <i className="bi bi-box-arrow-right me-1"></i>
            Log out
          </Button>
        </div>
      </Navbar>

      <Container className="flex-grow-1 d-flex flex-column py-5">
        <div className="text-center mb-5">
          <h1 className="dashboard-title fw-bold">Hospital Analytics Dashboard</h1>
          <p className="dashboard-subtitle">Select a metric to explore detailed insights.</p>
        </div>

        <Row className="g-4 justify-content-center flex-grow-1 align-content-center">
          {metrics.map((metric) => (
            <Col key={metric.path} xs={12} sm={6} lg={3}>
              <Card
                role="button"
                tabIndex={0}
                className="metric-card h-100 text-center border-0 shadow-sm rounded-4"
                onClick={() => navigate(metric.path)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') navigate(metric.path);
                }}
                style={{ borderTopColor: metric.color }}
              >
                <Card.Body className="d-flex flex-column align-items-center justify-content-center p-4">
                  <div
                    className="metric-icon-wrapper mb-3"
                    style={{ backgroundColor: `${metric.color}1a`, color: metric.color }}
                  >
                    <i className={`bi ${metric.icon}`}></i>
                  </div>
                  <Card.Title className="fs-6 fw-semibold mb-0" style={{ color: metric.color }}>
                    {metric.title}
                  </Card.Title>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      </Container>
    </div>
  );
}

export default Dashboard;

