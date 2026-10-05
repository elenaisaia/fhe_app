import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Button, Navbar, Card, Spinner } from 'react-bootstrap';
import { generateStatistics } from '../api/statistics';

function MetricPage({ title, icon, color, description, children, generateEndpoint }) {
  const navigate = useNavigate();
  const [generating, setGenerating] = useState(false);

  const handleGenerate = async () => {
    if (!generateEndpoint) return;
    setGenerating(true);
    try {
      await generateStatistics(generateEndpoint);
      alert(`Statistics generated for ${title.toLowerCase()}.`);
    } catch (error) {
      alert(`Could not generate statistics for ${title.toLowerCase()}: ${error.message}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="dashboard-page d-flex flex-column min-vh-100">
      <Navbar className="app-navbar shadow-sm px-3">
        <Navbar.Brand
          role="button"
          className="d-flex align-items-center gap-2 fw-bold"
          onClick={() => navigate('/dashboard')}
        >
          <i className="bi bi-activity"></i>
          MedIntel
        </Navbar.Brand>
        <div className="ms-auto">
          <Button variant="light" size="sm" onClick={() => navigate('/dashboard')}>
            <i className="bi bi-arrow-left me-1"></i>
            Back to dashboard
          </Button>
        </div>
      </Navbar>

      <Container className="flex-grow-1 py-5">
        <div className="text-center mb-4">
          <div
            className="metric-icon-wrapper mx-auto mb-3"
            style={{ backgroundColor: `${color}1a`, color }}
          >
            <i className={`bi ${icon}`}></i>
          </div>
          <h1 className="metric-page-title fw-bold" style={{ color }}>{title}</h1>
          <p className="metric-page-description text-muted">{description}</p>
          <Button
            size="lg"
            className="generate-btn px-5 py-3 rounded-pill shadow mt-2"
            onClick={handleGenerate}
            disabled={generating}
          >
            {generating ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Generating…
              </>
            ) : (
              <>
                <i className="bi bi-graph-up-arrow me-2"></i>
                Generate statistics
              </>
            )}
          </Button>
        </div>

        <Card className="border-0 shadow-sm rounded-4">
          <Card.Body className="p-4 p-md-5">
            {children ? (
              children
            ) : (
              <div className="text-center text-muted">
                <i className="bi bi-bar-chart-line display-4 d-block mb-3" style={{ color }}></i>
                <p className="mb-0">
                  Detailed analytics and charts for <strong>{title.toLowerCase()}</strong> will be
                  displayed here.
                </p>
              </div>
            )}
          </Card.Body>
        </Card>
      </Container>
    </div>
  );
}

export default MetricPage;

