'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Label } from '@/components/shadcn-ui/label';
import { Input } from '@/components/shadcn-ui/input';

interface ActiveDatesSectionProps {
  startsAt: string;
  endsAt?: string;
  onStartsAtChange: (date: string) => void;
  onEndsAtChange: (date: string | undefined) => void;
}

export function ActiveDatesSection({
  startsAt,
  endsAt,
  onStartsAtChange,
  onEndsAtChange,
}: ActiveDatesSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Active dates</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="start-date">Start date</Label>
            <Input
              id="start-date"
              type="datetime-local"
              value={startsAt}
              onChange={(e) => onStartsAtChange(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="start-time">Start time</Label>
            <Input
              id="start-time"
              type="time"
              value={startsAt ? new Date(startsAt).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' }) : ''}
              onChange={(e) => {
                const currentDate = new Date(startsAt);
                const [hours, minutes] = e.target.value.split(':');
                currentDate.setHours(Number(hours), Number(minutes));
                onStartsAtChange(currentDate.toISOString());
              }}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="end-date">Set end date (optional)</Label>
          <div className="grid grid-cols-2 gap-4">
            <Input
              id="end-date"
              type="datetime-local"
              value={endsAt || ''}
              onChange={(e) => onEndsAtChange(e.target.value || undefined)}
            />
            {endsAt && (
              <Input
                id="end-time"
                type="time"
                value={new Date(endsAt).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' })}
                onChange={(e) => {
                  const currentDate = new Date(endsAt);
                  const [hours, minutes] = e.target.value.split(':');
                  currentDate.setHours(Number(hours), Number(minutes));
                  onEndsAtChange(currentDate.toISOString());
                }}
              />
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
