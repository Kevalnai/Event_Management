import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import EventCard from './EventCard';

const baseEvent = {
  event_id: 'evt-1',
  title: 'Rooftop Sunset Sessions',
  venue: 'The Attic',
  start_date: '2027-06-01T18:00:00Z',
  price: 0,
  currency: 'USD',
  banner_url: null,
};

function renderCard(event) {
  return render(
    <MemoryRouter>
      <EventCard event={event} />
    </MemoryRouter>
  );
}

describe('EventCard', () => {
  it('shows "Free" for a zero-price event', () => {
    renderCard(baseEvent);
    expect(screen.getByText('Free')).toBeInTheDocument();
    expect(screen.getByText('Rooftop Sunset Sessions')).toBeInTheDocument();
    expect(screen.getByText('The Attic')).toBeInTheDocument();
  });

  it('shows the formatted price for a paid event', () => {
    renderCard({ ...baseEvent, price: 25, currency: 'USD' });
    expect(screen.getByText('$25.00')).toBeInTheDocument();
  });

  it('links to the event detail page', () => {
    renderCard(baseEvent);
    expect(screen.getByRole('link')).toHaveAttribute('href', '/events/evt-1');
  });

  it('falls back to a generated cover when banner_url is not a real URL', () => {
    const { container } = renderCard({ ...baseEvent, banner_url: 'string' });
    const cover = container.querySelector('[style*="background-image"]');
    expect(cover).toBeNull();
  });

  it('uses the banner image when banner_url is a real URL', () => {
    const { container } = renderCard({ ...baseEvent, banner_url: 'https://example.com/b.jpg' });
    const cover = container.querySelector('[style*="background-image"]');
    expect(cover).not.toBeNull();
  });
});
