'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Button } from '@/components/shadcn-ui/button';
import { Separator } from '@/components/shadcn-ui/separator';
import { Textarea } from '@/components/shadcn-ui/textarea';
import { FileText } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

export interface TimelineEvent {
  id: string;
  type: string;
  message: string;
  createdAt: string;
  author?: {
    name: string;
    avatarUrl?: string;
    initials: string;
  };
  metadata?: Record<string, any>;
}

interface CustomerTimelineProps {
  events: TimelineEvent[];
  onCommentAdded?: () => void;
}

export function CustomerTimeline({ events = [], onCommentAdded }: CustomerTimelineProps) {
  const [comment, setComment] = useState('');

  // Sort events: Newest first
  const sortedEvents = [...events].sort((a, b) =>
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );

  const handlePostComment = () => {
    // Placeholder until mutation is ready
    if (!comment.trim()) return;
    toast.info('Notes functionality coming soon!');
    setComment('');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Comment Input */}
          <div className="flex gap-3">
            <div className="h-8 w-8 rounded bg-pink-500 flex items-center justify-center text-white text-sm font-medium flex-shrink-0">
              AS
            </div>
            <div className="flex-1">
              <Textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Leave a note..."
                className="min-h-[80px] resize-none"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handlePostComment();
                  }
                }}
              />
              <div className="flex items-center justify-between mt-2">
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <FileText className="h-4 w-4" />
                  </Button>
                </div>
                <Button size="sm" variant="ghost" onClick={handlePostComment} disabled={!comment.trim()}>
                  Post
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Only you and other staff can see notes
              </p>
            </div>
          </div>

          <Separator />

          {/* Timeline Feed */}
          <div className="relative pl-4 border-l-2 border-muted space-y-8">
            {sortedEvents.length === 0 && (
              <p className="text-sm text-muted-foreground pl-4">No history yet.</p>
            )}

            {sortedEvents.map((event) => {
              const date = new Date(event.createdAt);

              // Determine icon/color based on content (simple heuristic)
              const isOrderEvent = event.message.includes('Order');
              const isMarketing = event.message.includes('arketi'); // Marketing

              return (
                <div key={event.id} className="relative">
                  <div className="flex items-start gap-4">
                    {/* Timeline Dot */}
                    <div className={`absolute -left-[21px] top-1 h-3 w-3 rounded-full border-2 border-background ${isOrderEvent ? 'bg-blue-500' : isMarketing ? 'bg-purple-500' : 'bg-gray-400'
                      }`} />

                    {/* Content */}
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-foreground">
                          {event.author ? (
                            <span className="font-medium mr-1">{event.author.name}</span>
                          ) : (
                            <span className="font-medium mr-1 text-muted-foreground">System</span>
                          )}
                          {event.message}
                        </span>
                        <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
                          {format(date, 'MMM d, h:mm a')}
                        </span>
                      </div>

                      {/* Optional metadata display if needed */}
                      {event.metadata && event.metadata.total_price && (
                        <p className="text-xs text-muted-foreground">
                          Total: {event.metadata.currency || 'XAF'} {event.metadata.total_price}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
