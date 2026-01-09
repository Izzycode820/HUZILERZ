import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { format } from 'date-fns';
import { Button } from '@/components/shadcn-ui/button';
import { Input } from '@/components/shadcn-ui/input';
import { useMutation } from '@apollo/client/react';
import { AddOrderCommentDocument } from '@/services/graphql/admin-store/mutations/orders/__generated__/AddOrderComment.generated';
import { toast } from 'sonner';

export interface TimelineEvent {
  id: string;
  type: 'COMMENT' | 'STATUS_CHANGE' | 'NOTIFICATION' | 'ORDER_CREATED';
  message: string;
  createdAt: string;
  author?: {
    name: string;
    avatarUrl?: string;
    initials: string;
  };
  metadata?: Record<string, any>;
  isInternal?: boolean;
}

interface TimelineSectionProps {
  orderId: string;
  events: TimelineEvent[];
  onCommentAdded?: () => void;
}

export function TimelineSection({
  orderId,
  events = [],
  onCommentAdded,
}: TimelineSectionProps) {
  const [comment, setComment] = useState('');

  // Sorting events: Newest first
  const sortedEvents = [...events].sort((a, b) =>
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );

  // Mutation
  const [addComment, { loading: postingComment }] = useMutation(AddOrderCommentDocument);

  const handlePostComment = async () => {
    if (!comment.trim()) return;

    try {
      const result = await addComment({
        variables: {
          orderId,
          message: comment,
          isInternal: true
        }
      });

      if (result.data?.addOrderComment?.success) {
        toast.success('Comment posted');
        setComment('');
        onCommentAdded?.();
      } else {
        toast.error(result.data?.addOrderComment?.error || 'Failed to post comment');
      }
    } catch (error) {
      toast.error('An error occurred while posting comment');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Timeline</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Comment Input */}
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="relative">
              <Input
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Leave a comment..."
                className="pr-16"
                disabled={postingComment}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handlePostComment();
                  }
                }}
              />
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-8 text-muted-foreground hover:text-foreground"
                onClick={handlePostComment}
                disabled={postingComment || !comment.trim()}
              >
                Post
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2 text-right">
              Only you and other staff can see comments
            </p>
          </div>
        </div>

        {/* Timeline Feed */}
        <div className="relative pl-4 border-l-2 border-muted space-y-8">
          {sortedEvents.map((event, index) => {
            const date = new Date(event.createdAt);

            return (
              <div key={event.id} className="relative">
                <div className="flex items-start gap-4">
                  {/* Timeline Dot */}
                  <div className={`absolute -left-[21px] top-1 h-3 w-3 rounded-full border-2 border-background ${event.type === 'COMMENT' ? 'bg-blue-500' : 'bg-gray-300'
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

                    {/* Metadata / Specifics */}
                    {event.type === 'ORDER_CREATED' && event.metadata?.order_source && (
                      <p className="text-xs text-muted-foreground">
                        Order received from {event.metadata.order_source === 'whatsapp' ? 'WhatsApp' : event.metadata.order_source === 'payment' ? 'Payment Gateway' : 'Manual Entry'}
                      </p>
                    )}
                    {event.type === 'STATUS_CHANGE' && event.metadata && (
                      <p className="text-xs text-muted-foreground">
                        {event.metadata.old_status && event.metadata.new_status ?
                          `Changed from ${event.metadata.old_status} to ${event.metadata.new_status}` :
                          event.metadata.tracking_number ?
                            `Tracking: ${event.metadata.tracking_number}` :
                            ''
                        }
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
