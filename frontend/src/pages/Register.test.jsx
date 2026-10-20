import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import Register from './Register';

const mockRegister = vi.fn();
const mockNavigate = vi.fn();

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ register: mockRegister }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

beforeEach(() => {
  mockRegister.mockReset();
  mockNavigate.mockReset();
});

function renderRegister() {
  return render(
    <MemoryRouter>
      <Register />
    </MemoryRouter>
  );
}

describe('Register page', () => {
  it('submits username, email, and password to register()', async () => {
    mockRegister.mockResolvedValue({ ok: true });
    renderRegister();

    await userEvent.type(screen.getByLabelText('Username'), 'alice');
    await userEvent.type(screen.getByLabelText('Email'), 'alice@example.com');
    await userEvent.type(screen.getByLabelText(/Password/), 'Passw0rd!');
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

    expect(mockRegister).toHaveBeenCalledWith('alice', 'alice@example.com', 'Passw0rd!');
  });

  it('redirects to the dashboard on success', async () => {
    mockRegister.mockResolvedValue({ ok: true });
    renderRegister();

    await userEvent.type(screen.getByLabelText('Username'), 'alice');
    await userEvent.type(screen.getByLabelText('Email'), 'alice@example.com');
    await userEvent.type(screen.getByLabelText(/Password/), 'Passw0rd!');
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

    expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
  });

  it('shows the server error and does not navigate on failure', async () => {
    mockRegister.mockResolvedValue({ ok: false, message: 'Email already registered.' });
    renderRegister();

    await userEvent.type(screen.getByLabelText('Username'), 'alice');
    await userEvent.type(screen.getByLabelText('Email'), 'taken@example.com');
    await userEvent.type(screen.getByLabelText(/Password/), 'Passw0rd!');
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }));

    expect(await screen.findByText('Email already registered.')).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
