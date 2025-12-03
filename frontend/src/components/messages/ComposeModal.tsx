import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal, Input, Textarea, Button } from '../ui';
import { useSendMessage } from '../../services/messageAPI';
import { useToast } from '../ui/Toast';

const messageSchema = z.object({
    to_ve_id: z.string().min(1, 'VE is required'),
    subject: z.string().min(1, 'Subject is required').max(200),
    content: z.string().min(1, 'Message content is required'),
});

type MessageFormData = z.infer<typeof messageSchema>;

interface ComposeModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const ComposeModal: React.FC<ComposeModalProps> = ({ isOpen, onClose }) => {
    const { addToast } = useToast();
    const sendMessage = useSendMessage();
    const {
        register,
        handleSubmit,
        formState: { errors },
        reset,
    } = useForm<MessageFormData>({
        resolver: zodResolver(messageSchema),
    });

    const onSubmit = async (data: MessageFormData) => {
        try {
            await sendMessage.mutateAsync(data);
            addToast('success', 'Message sent successfully!');
            reset();
            onClose();
        } catch (error) {
            addToast('error', 'Failed to send message');
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Compose Message"
            description="Send a message to your VE"
            size="lg"
        >
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <Input
                    label="To (VE ID)"
                    placeholder="Enter VE ID"
                    error={errors.to_ve_id?.message}
                    {...register('to_ve_id')}
                />

                <Input
                    label="Subject"
                    placeholder="Enter subject"
                    error={errors.subject?.message}
                    {...register('subject')}
                />

                <Textarea
                    label="Message"
                    placeholder="Type your message here..."
                    rows={6}
                    error={errors.content?.message}
                    {...register('content')}
                />

                <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="outline" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button type="submit" isLoading={sendMessage.isPending}>
                        Send Message
                    </Button>
                </div>
            </form>
        </Modal>
    );
};
