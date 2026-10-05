import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Card,
  Form,
  Button,
  Navbar,
  Alert,
  InputGroup,
  Row,
  Col, Spinner,
} from 'react-bootstrap';

const EXPENSE_TYPES = ['Personnel', 'Supplies', 'Medicine', 'Equipment'];

function ExpenseEntry() {
  const navigate = useNavigate();

  const [expense, setExpense] = useState({
    description: '',
    amount: '',
    date: '',
    expenseType: '',
  });
  const [feedback, setFeedback] = useState(null);
  const [validated, setValidated] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const {description, amount, date, expenseType} = expense;

    if (!description || !amount || !date || !expenseType) {
      setFeedback({variant: 'danger', message: 'Please fill in all fields to add an expense.'});
      return;
    }
    if (Number(amount) <= 0) {
      setFeedback({variant: 'danger', message: 'Amount must be greater than 0.'});
      return;
    }

    setFeedback({
      variant: 'success',
      message: `Expense recorded: ${expenseType} — €${Number(amount).toLocaleString('de-DE', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })} on ${date} ("${description}").`,
    });
    setExpense({description: '', amount: '', date: '', expenseType: ''});

    setValidated(true);
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/expenses/add', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: description,
          expenseDate: date,
          expenseType: expenseType,
          amount: amount,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Error occurred in adding expense. Please try again later.');
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
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

      <Container className="flex-grow-1 py-5" style={{ maxWidth: '640px' }}>
        <div className="text-center mb-5">
          <div
            className="metric-icon-wrapper mx-auto mb-3"
            style={{ backgroundColor: '#fd7e141a', color: '#fd7e14' }}
          >
            <i className="bi bi-receipt"></i>
          </div>
          <h1 className="fw-bold">Hospital expenses</h1>
          <p className="text-muted">Record a new hospital expense.</p>
        </div>

        <Card className="border-0 shadow-sm rounded-4">
          <Card.Body className="p-4 p-md-5">
            <h5 className="fw-semibold mb-3">
              <i className="bi bi-plus-circle me-2 text-primary"></i>
              Add an expense
            </h5>

            {error && (
                <Alert variant="danger">
                  {error}
                </Alert>
            )}

            <Form validated={validated} onSubmit={handleSubmit}>
              <Form.Group className="mb-3">
                <Form.Label>Description</Form.Label>
                <Form.Control
                  value={expense.description}
                  onChange={(e) => setExpense({ ...expense, description: e.target.value })}
                  placeholder="e.g. New ECG monitors for Cardiology"
                />
              </Form.Group>

              <Row className="g-3">
                <Col md={6}>
                  <Form.Group>
                    <Form.Label>Amount</Form.Label>
                    <InputGroup>
                      <InputGroup.Text>€</InputGroup.Text>
                      <Form.Control
                        type="number"
                        min="0"
                        step="0.01"
                        value={expense.amount}
                        onChange={(e) => setExpense({ ...expense, amount: e.target.value })}
                        placeholder="0.00"
                      />
                    </InputGroup>
                  </Form.Group>
                </Col>
                <Col md={6}>
                  <Form.Group>
                    <Form.Label>Date</Form.Label>
                    <Form.Control
                      type="date"
                      value={expense.date}
                      onChange={(e) => setExpense({ ...expense, date: e.target.value })}
                    />
                  </Form.Group>
                </Col>
              </Row>

              <Form.Group className="mt-3 mb-2">
                <Form.Label>Expense type</Form.Label>
                <Form.Select
                  value={expense.expenseType}
                  onChange={(e) => setExpense({ ...expense, expenseType: e.target.value })}
                >
                  <option value="">Select expense type…</option>
                  {EXPENSE_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>

              <Button type="submit" variant="primary" className="mt-3" disabled={loading}>
                {loading ? (
                    <>
                      <Spinner animation="border" size="sm" className="me-2"/>
                      Adding expense...
                    </>
                ) : (
                    'Add expense'
                )}
              </Button>
            </Form>

            {feedback && (
              <Alert variant={feedback.variant} className="mt-3 mb-0 py-2">
                {feedback.message}
              </Alert>
            )}
          </Card.Body>
        </Card>
      </Container>
    </div>
  );
}

export default ExpenseEntry;

