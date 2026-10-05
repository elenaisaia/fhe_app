import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {Form, Button, Card, Container, InputGroup, Alert, Spinner} from 'react-bootstrap';

function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [validated, setValidated] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    if (form.checkValidity() === false) {
      event.stopPropagation();
      setValidated(true);
      return;
    }


    setValidated(true);
    setError('');
    setLoading(true);


    try {
      const response = await fetch('http://127.0.0.1:8000/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          password: password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Invalid credentials.');
      }

      const userType = data.userType;

      if (userType === 'medical') {
        navigate('/patient-operations');
      } else if (userType === 'accounting') {
        navigate('/expense-entry');
      } else if (userType === 'management') {
        navigate('/dashboard');
      } else {
        throw new Error('Unknown user type.');
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="login-page d-flex align-items-center justify-content-center">
      <Container style={{ maxWidth: '420px' }}>
        <div className="text-center mb-4 text-white">
          <i className="bi bi-activity brand-icon"></i>
          <h1 className="brand-title mb-0">MedIntel</h1>
          <p className="brand-subtitle mb-0">
            Hospital Intelligence Platform
          </p>
        </div>

        <Card className="shadow-lg border-0 rounded-4">
          <Card.Body className="p-4 p-md-5">
            <h4 className="mb-4 text-center fw-semibold">Sign in</h4>

            {error && (
                <Alert variant="danger">
                  {error}
                </Alert>
            )}

            <Form noValidate validated={validated} onSubmit={handleSubmit}>
              <Form.Group className="mb-3" controlId="loginUsername">
                <Form.Label>Username</Form.Label>
                <InputGroup>
                  <InputGroup.Text>
                    <i className="bi bi-person"></i>
                  </InputGroup.Text>

                  <Form.Control type="text" placeholder="Enter username" value={username} onChange={(e) => setUsername(e.target.value)} required/>

                  <Form.Control.Feedback type="invalid">
                    Please enter your username.
                  </Form.Control.Feedback>
                </InputGroup>
              </Form.Group>

              <Form.Group className="mb-4" controlId="loginPassword">
                <Form.Label>Password</Form.Label>
                <InputGroup>
                  <InputGroup.Text>
                    <i className="bi bi-lock"></i>
                  </InputGroup.Text>

                  <Form.Control type="password" placeholder="Enter password" value={password} onChange={(e) => setPassword(e.target.value)} required/>

                  <Form.Control.Feedback type="invalid">
                    Please enter your password.
                  </Form.Control.Feedback>
                </InputGroup>
              </Form.Group>

              <Button type="submit" variant="primary" size="lg" className="w-100" disabled={loading}>
                {loading ? (
                    <>
                      <Spinner animation="border" size="sm" className="me-2"/>
                      Logging in...
                    </>
                ) : (
                    'Log in'
                )}
              </Button>
            </Form>
          </Card.Body>
        </Card>

        <p className="text-center text-white-50 mt-4 mb-0 small">
          &copy; {new Date().getFullYear()} MedIntel. For authorized hospital
          management only.
        </p>
      </Container>
    </div>
  );
}

export default Login;
