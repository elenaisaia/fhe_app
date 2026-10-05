import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Row,
  Col,
  Card,
  Form,
  Button,
  Navbar,
  Alert,
  InputGroup,
  Spinner,
} from 'react-bootstrap';

const WARDS = [
  'ICU',
  'ER',
  'Surgery',
  'General',
];

const COST_TYPES = ['Medical services', 'Hospitalization', 'Meds', 'Meals'];

function PatientOperations() {
  const navigate = useNavigate();

  const [feedback, setFeedback] = useState({});
  const [loading, setLoading] = useState({});

  // --- Operation form state ---------------------------------------------
  const [admit, setAdmit] = useState({
    id: '',
    name: '',
    age: '',
    diagnosis: '',
    admissionDate: '',
    ward: '',
  });

  const [chart, setChart] = useState({
    id: '',
    diagnosis: '',
    ward: '',
  });

  const [cost, setCost] = useState({
    id: '',
    amount: '',
    costType: '',
  });

  const [discharge, setDischarge] = useState({
    id: '',
    date: '',
  });

  const [death, setDeath] = useState({
    id: '',
    date: '',
  });


  const setSectionLoading = (key, value) => {
    setLoading((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const showFeedback = (key, variant, message) => {
    setFeedback((prev) => ({
      ...prev,
      [key]: {
        variant,
        message,
      },
    }));
  };

  const clearFeedback = (key) => {
    setFeedback((prev) => {
      const updated = { ...prev };
      delete updated[key];
      return updated;
    });
  };

  const renderFeedback = (key) => {
    const fb = feedback[key];

    if (!fb) return null;

    return (
        <Alert variant={fb.variant} className="mt-3 mb-0 py-2">
          {fb.message}
        </Alert>
    );
  };

  const getBackendErrorMessage = async (response) => {
    try {
      const data = await response.json();

      if (data.message) {
        return data.message;
      }

      if (data.detail) {
        if (typeof data.detail === 'string') {
          return data.detail;
        }

        if (Array.isArray(data.detail)) {
          return data.detail
              .map((err) => err.msg || JSON.stringify(err))
              .join(', ');
        }

        return JSON.stringify(data.detail);
      }

      return 'An unexpected error occurred.';
    } catch {
      return 'An unexpected error occurred.';
    }
  };

  const getAgeCategoryFromAge = (age) => {
    const numericAge = Number(age);

    if (numericAge < 18) return 'under 18';
    if (numericAge > 65) return 'over 65';

    return '18 to 65';
  };


  const handleAdmit = async (e) => {
    e.preventDefault();

    const { id, name, age, diagnosis, admissionDate, ward } = admit;

    if (!id || !name || !age || !diagnosis || !admissionDate || !ward) {
      showFeedback('admit', 'danger', 'Please fill in all fields to admit a patient.');
      return;
    }

    clearFeedback('admit');
    setSectionLoading('admit', true);

    try {
      const response = await fetch('http://127.0.0.1:8000/hospitalizations/add', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patientId: id,
          name,
          ageCategory: getAgeCategoryFromAge(age),
          diagnosis,
          ward,
          admissionDate,
        }),
      });

      if (!response.ok) {
        const message = await getBackendErrorMessage(response);
        throw new Error(message);
      }

      const data = await response.json();

      showFeedback(
          'admit',
          'success',
          data.message ||
          `Patient ${name} (ID ${id}) admitted to ${ward} on ${admissionDate} with diagnosis "${diagnosis}".`
      );

      setAdmit({
        id: '',
        name: '',
        age: '',
        diagnosis: '',
        admissionDate: '',
        ward: '',
      });
    } catch (error) {
      showFeedback('admit', 'danger', error.message);
    } finally {
      setSectionLoading('admit', false);
    }
  };

  const handleChartUpdate = async (e) => {
    e.preventDefault();

    const { id, diagnosis, ward } = chart;

    if (!id) {
      showFeedback('chart', 'danger', "Please enter the patient's ID.");
      return;
    }

    if (!diagnosis && !ward) {
      showFeedback('chart', 'danger', 'Provide at least one field to update: diagnosis or ward.');
      return;
    }

    clearFeedback('chart');
    setSectionLoading('chart', true);

    try {
      const response = await fetch('http://127.0.0.1:8000/hospitalizations/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patientId: id,
          diagnosis: diagnosis || null,
          ward: ward || null,
        }),
      });

      if (!response.ok) {
        const message = await getBackendErrorMessage(response);
        throw new Error(message);
      }

      const data = await response.json();

      const changes = [];
      if (diagnosis) changes.push(`diagnosis → "${diagnosis}"`);
      if (ward) changes.push(`ward → ${ward}`);

      showFeedback(
          'chart',
          'success',
          data.message || `Chart for patient ${id} updated: ${changes.join(', ')}.`
      );

      setChart({
        id: '',
        diagnosis: '',
        ward: '',
      });
    } catch (error) {
      showFeedback('chart', 'danger', error.message);
    } finally {
      setSectionLoading('chart', false);
    }
  };

  const handleAddCost = async (e) => {
    e.preventDefault();

    const { id, amount, costType } = cost;

    if (!id || !amount || !costType) {
      showFeedback('cost', 'danger', 'Please enter the patient ID, an amount and select a cost type.');
      return;
    }

    if (Number(amount) <= 0) {
      showFeedback('cost', 'danger', 'Amount must be greater than 0.');
      return;
    }

    const getCostOfType = (type) => {
      return costType === type ? Number(amount) : 0;
    };

    clearFeedback('cost');
    setSectionLoading('cost', true);

    try {
      const response = await fetch('http://127.0.0.1:8000/hospitalizations/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patientId: id,
          costServices: getCostOfType('Medical services'),
          costHospitalization: getCostOfType('Hospitalization'),
          costMeds: getCostOfType('Meds'),
          costMeals: getCostOfType('Meals'),
        }),
      });

      if (!response.ok) {
        const message = await getBackendErrorMessage(response);
        throw new Error(message);
      }

      const data = await response.json();

      showFeedback(
          'cost',
          'success',
          data.message ||
          `Added €${Number(amount).toLocaleString('de-DE')} (${costType}) to patient ${id}'s chart.`
      );

      setCost({
        id: '',
        amount: '',
        costType: '',
      });
    } catch (error) {
      showFeedback('cost', 'danger', error.message);
    } finally {
      setSectionLoading('cost', false);
    }
  };

  const handleDischarge = async (e) => {
    e.preventDefault();

    if (!discharge.id) {
      showFeedback('discharge', 'danger', "Please enter the patient's ID.");
      return;
    }

    if (!discharge.date) {
      showFeedback('discharge', 'danger', "Please enter the patient's discharge date.");
      return;
    }

    clearFeedback('discharge');
    setSectionLoading('discharge', true);

    try {
      const response = await fetch('http://127.0.0.1:8000/hospitalizations/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patientId: discharge.id,
          dischargeDate: discharge.date,
        }),
      });

      if (!response.ok) {
        const message = await getBackendErrorMessage(response);
        throw new Error(message);
      }

      const data = await response.json();

      showFeedback(
          'discharge',
          'success',
          data.message || `Patient ${discharge.id} has been discharged on ${discharge.date}.`
      );

      setDischarge({
        id: '',
        date: '',
      });
    } catch (error) {
      showFeedback('discharge', 'danger', error.message);
    } finally {
      setSectionLoading('discharge', false);
    }
  };

  const handleDeath = async (e) => {
    e.preventDefault();

    if (!death.id) {
      showFeedback('death', 'danger', "Please enter the patient's ID.");
      return;
    }

    if (!death.date) {
      showFeedback('death', 'danger', "Please enter the patient's date of death.");
      return;
    }

    clearFeedback('death');
    setSectionLoading('death', true);

    try {
      const response = await fetch('http://127.0.0.1:8000/hospitalizations/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patientId: death.id,
          dischargeDate: death.date,
          died: true,
        }),
      });

      if (!response.ok) {
        const message = await getBackendErrorMessage(response);
        throw new Error(message);
      }

      const data = await response.json();

      showFeedback(
          'death',
          'success',
          data.message || `Death of patient ${death.id} has been recorded on ${death.date}.`
      );

      setDeath({
        id: '',
        date: '',
      });
    } catch (error) {
      showFeedback('death', 'danger', error.message);
    } finally {
      setSectionLoading('death', false);
    }
  };

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

        <Container className="flex-grow-1 py-5">
          <div className="text-center mb-5">
            <div
                className="metric-icon-wrapper mx-auto mb-3"
                style={{ backgroundColor: '#0d6efd1a', color: '#0d6efd' }}
            >
              <i className="bi bi-clipboard2-pulse"></i>
            </div>

            <h1 className="fw-bold">Patient operations</h1>
            <p className="text-muted">Admit, update, discharge and record patient records.</p>
          </div>

          <Row className="g-4">
            {/* 1. Admit a new patient */}
            <Col xs={12}>
              <Card className="border-0 shadow-sm rounded-4">
                <Card.Body className="p-4">
                  <h5 className="fw-semibold mb-3">
                    <i className="bi bi-person-plus me-2 text-primary"></i>
                    Admit a new patient
                  </h5>

                  <Form onSubmit={handleAdmit}>
                    <Row className="g-3">
                      <Col md={4}>
                        <Form.Label>Patient ID</Form.Label>
                        <Form.Control
                            value={admit.id}
                            onChange={(e) => setAdmit({ ...admit, id: e.target.value })}
                            placeholder="e.g. P-10234"
                        />
                      </Col>

                      <Col md={4}>
                        <Form.Label>Name</Form.Label>
                        <Form.Control
                            value={admit.name}
                            onChange={(e) => setAdmit({ ...admit, name: e.target.value })}
                            placeholder="Full name"
                        />
                      </Col>

                      <Col md={4}>
                        <Form.Label>Age</Form.Label>
                        <Form.Control
                            type="number"
                            min="0"
                            value={admit.age}
                            onChange={(e) => setAdmit({ ...admit, age: e.target.value })}
                            placeholder="Age"
                        />
                      </Col>

                      <Col md={4}>
                        <Form.Label>Diagnosis</Form.Label>
                        <Form.Control
                            value={admit.diagnosis}
                            onChange={(e) => setAdmit({ ...admit, diagnosis: e.target.value })}
                            placeholder="Diagnosis"
                        />
                      </Col>

                      <Col md={4}>
                        <Form.Label>Admission day</Form.Label>
                        <Form.Control
                            type="date"
                            value={admit.admissionDate}
                            onChange={(e) => setAdmit({ ...admit, admissionDate: e.target.value })}
                        />
                      </Col>

                      <Col md={4}>
                        <Form.Label>Ward</Form.Label>
                        <Form.Select
                            value={admit.ward}
                            onChange={(e) => setAdmit({ ...admit, ward: e.target.value })}
                        >
                          <option value="">Select ward…</option>
                          {WARDS.map((w) => (
                              <option key={w} value={w}>
                                {w}
                              </option>
                          ))}
                        </Form.Select>
                      </Col>
                    </Row>

                    <Button
                        type="submit"
                        variant="primary"
                        className="mt-3"
                        disabled={loading.admit}
                    >
                      {loading.admit ? (
                          <>
                            <Spinner animation="border" size="sm" className="me-2" />
                            Admitting patient...
                          </>
                      ) : (
                          'Admit patient'
                      )}
                    </Button>
                  </Form>

                  {renderFeedback('admit')}
                </Card.Body>
              </Card>
            </Col>

            {/* 2. Update chart: diagnosis / ward */}
            <Col md={6}>
              <Card className="border-0 shadow-sm rounded-4 h-100">
                <Card.Body className="p-4">
                  <h5 className="fw-semibold mb-3">
                    <i className="bi bi-pencil-square me-2 text-primary"></i>
                    Update patient chart
                  </h5>

                  <Form onSubmit={handleChartUpdate}>
                    <Form.Group className="mb-3">
                      <Form.Label>Patient ID</Form.Label>
                      <Form.Control
                          value={chart.id}
                          onChange={(e) => setChart({ ...chart, id: e.target.value })}
                          placeholder="e.g. P-10234"
                      />
                    </Form.Group>

                    <Form.Group className="mb-3">
                      <Form.Label>Diagnosis optional</Form.Label>
                      <Form.Control
                          value={chart.diagnosis}
                          onChange={(e) => setChart({ ...chart, diagnosis: e.target.value })}
                          placeholder="New diagnosis"
                      />
                    </Form.Group>

                    <Form.Group className="mb-2">
                      <Form.Label>Ward optional</Form.Label>
                      <Form.Select
                          value={chart.ward}
                          onChange={(e) => setChart({ ...chart, ward: e.target.value })}
                      >
                        <option value="">Keep current ward…</option>
                        {WARDS.map((w) => (
                            <option key={w} value={w}>
                              {w}
                            </option>
                        ))}
                      </Form.Select>
                    </Form.Group>

                    <Form.Text className="text-muted">
                      Provide the ID plus at least one field to update.
                    </Form.Text>

                    <div>
                      <Button
                          type="submit"
                          variant="primary"
                          className="mt-3"
                          disabled={loading.chart}
                      >
                        {loading.chart ? (
                            <>
                              <Spinner animation="border" size="sm" className="me-2" />
                              Updating chart...
                            </>
                        ) : (
                            'Update chart'
                        )}
                      </Button>
                    </div>
                  </Form>

                  {renderFeedback('chart')}
                </Card.Body>
              </Card>
            </Col>

            {/* 3. Add a cost */}
            <Col md={6}>
              <Card className="border-0 shadow-sm rounded-4 h-100">
                <Card.Body className="p-4">
                  <h5 className="fw-semibold mb-3">
                    <i className="bi bi-cash-coin me-2 text-primary"></i>
                    Add a cost to a chart
                  </h5>

                  <Form onSubmit={handleAddCost}>
                    <Form.Group className="mb-3">
                      <Form.Label>Patient ID</Form.Label>
                      <Form.Control
                          value={cost.id}
                          onChange={(e) => setCost({ ...cost, id: e.target.value })}
                          placeholder="e.g. P-10234"
                      />
                    </Form.Group>

                    <Form.Group className="mb-3">
                      <Form.Label>Amount</Form.Label>
                      <InputGroup>
                        <InputGroup.Text>€</InputGroup.Text>
                        <Form.Control
                            type="number"
                            min="0"
                            step="0.01"
                            value={cost.amount}
                            onChange={(e) => setCost({ ...cost, amount: e.target.value })}
                            placeholder="0.00"
                        />
                      </InputGroup>
                    </Form.Group>

                    <Form.Group className="mb-2">
                      <Form.Label>Cost type</Form.Label>
                      <Form.Select
                          value={cost.costType}
                          onChange={(e) => setCost({ ...cost, costType: e.target.value })}
                      >
                        <option value="">Select cost type…</option>
                        {COST_TYPES.map((t) => (
                            <option key={t} value={t}>
                              {t}
                            </option>
                        ))}
                      </Form.Select>
                    </Form.Group>

                    <div>
                      <Button
                          type="submit"
                          variant="primary"
                          className="mt-3"
                          disabled={loading.cost}
                      >
                        {loading.cost ? (
                            <>
                              <Spinner animation="border" size="sm" className="me-2" />
                              Adding cost...
                            </>
                        ) : (
                            'Add cost'
                        )}
                      </Button>
                    </div>
                  </Form>

                  {renderFeedback('cost')}
                </Card.Body>
              </Card>
            </Col>

            {/* 4. Discharge a patient */}
            <Col md={6}>
              <Card className="border-0 shadow-sm rounded-4 h-100">
                <Card.Body className="p-4">
                  <h5 className="fw-semibold mb-3">
                    <i className="bi bi-box-arrow-right me-2 text-success"></i>
                    Discharge a patient
                  </h5>

                  <Form onSubmit={handleDischarge}>
                    <Form.Group className="mb-2">
                      <Form.Label>Patient ID</Form.Label>
                      <Form.Control
                          value={discharge.id}
                          onChange={(e) => setDischarge({ ...discharge, id: e.target.value })}
                          placeholder="e.g. P-10234"
                      />
                    </Form.Group>

                    <Form.Group className="mb-2">
                      <Form.Label>Discharge date</Form.Label>
                      <Form.Control
                          type="date"
                          value={discharge.date}
                          onChange={(e) => setDischarge({ ...discharge, date: e.target.value })}
                      />
                    </Form.Group>

                    <Button
                        type="submit"
                        variant="primary"
                        className="mt-3"
                        disabled={loading.discharge}
                    >
                      {loading.discharge ? (
                          <>
                            <Spinner animation="border" size="sm" className="me-2" />
                            Discharging patient...
                          </>
                      ) : (
                          'Discharge patient'
                      )}
                    </Button>
                  </Form>

                  {renderFeedback('discharge')}
                </Card.Body>
              </Card>
            </Col>

            {/* 5. Declare death */}
            <Col md={6}>
              <Card className="border-0 shadow-sm rounded-4 h-100">
                <Card.Body className="p-4">
                  <h5 className="fw-semibold mb-3">
                    <i className="bi bi-heartbreak me-2 text-danger"></i>
                    Declare death of a patient
                  </h5>

                  <Form onSubmit={handleDeath}>
                    <Form.Group className="mb-3">
                      <Form.Label>Patient ID</Form.Label>
                      <Form.Control
                          value={death.id}
                          onChange={(e) => setDeath({ ...death, id: e.target.value })}
                          placeholder="e.g. P-10234"
                      />
                    </Form.Group>

                    <Form.Group className="mb-2">
                      <Form.Label>Date of death</Form.Label>
                      <Form.Control
                          type="date"
                          value={death.date}
                          onChange={(e) => setDeath({ ...death, date: e.target.value })}
                      />
                    </Form.Group>

                    <Button
                        type="submit"
                        variant="primary"
                        className="mt-3"
                        disabled={loading.death}
                    >
                      {loading.death ? (
                          <>
                            <Spinner animation="border" size="sm" className="me-2" />
                            Declaring death...
                          </>
                      ) : (
                          'Declare death'
                      )}
                    </Button>
                  </Form>

                  {renderFeedback('death')}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Container>
      </div>
  );
}

export default PatientOperations;