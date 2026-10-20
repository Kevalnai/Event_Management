import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import Button from './Button';

describe('Button', () => {
  it('renders as a native button and responds to clicks', async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click me</Button>);

    const btn = screen.getByRole('button', { name: 'Click me' });
    await userEvent.click(btn);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('renders as a router Link when given a "to" prop', () => {
    render(
      <MemoryRouter>
        <Button to="/events">Browse</Button>
      </MemoryRouter>
    );
    const link = screen.getByRole('link', { name: 'Browse' });
    expect(link).toHaveAttribute('href', '/events');
  });

  it('renders as a plain anchor when given an "href" prop', () => {
    render(<Button href="https://example.com">External</Button>);
    const link = screen.getByRole('link', { name: 'External' });
    expect(link).toHaveAttribute('href', 'https://example.com');
  });

  it('disables the native button when "disabled" is set', () => {
    render(<Button disabled>Can't click</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
