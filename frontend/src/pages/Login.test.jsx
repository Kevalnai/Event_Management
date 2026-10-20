import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import Login from './Login';

const mockLogin = vi.fn();
const mockNavigate = vi.fn();

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ login: mockLogin }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ state: null }),
  };
});

beforeEach(() => {
  mockLogin.mockReset();
  mockNavigate.mockReset();
});

function renderLogin() {
  return render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>
  );
}

describe('Login page', () => {
  it('submits the identifier and password to login()', async () => {
    mockLogin.mockResolvedValue({ ok: true });
    renderLogin();

    await userEvent.type(screen.getByLabelText('Email or username'), 'alice@example.com');
    await userEvent.type(screen.getByLabelText('Password'), 'Passw0rd!');
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }));

    expect(mockLogin).toHaveBeenCalledWith('alice@example.com', 'Passw0rd!');
  });

  it('redirects to the dashboard after a successful login', async () => {
    mockLogin.mockResolvedValue({ ok: true });
    renderLogin();

    await userEvent.type(screen.getByLabelText('Email or username'), 'alice');
    await userEvent.type(screen.getByLabelText('Password'), 'Passw0rd!');
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }));

    expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
  });

  it('shows the server error message and does not navigate on failure', async () => {
    mockLogin.mockResolvedValue({ ok: false, message: 'Invalid credentials.' });
    renderLogin();

    await userEvent.type(screen.getByLabelText('Email or username'), 'alice');
    await userEvent.type(screen.getByLabelText('Password'), 'wrong');
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }));

    expect(await screen.findByText('Invalid credentials.')).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
