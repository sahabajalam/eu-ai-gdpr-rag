
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Reference {
    text: string;
    metadata: {
        title: string;
        article_number: string;
        regulation: string;
        source?: string;
    };
    score?: number;
}

interface DeepDiveModalProps {
    reference: Reference | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function DeepDiveModal({ reference, open, onOpenChange }: DeepDiveModalProps) {
    if (!reference) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl h-[80vh] flex flex-col">
                <DialogHeader>
                    <DialogTitle className="text-xl">
                        {reference.metadata.regulation} - Article {reference.metadata.article_number}
                    </DialogTitle>
                    <DialogDescription className="text-base font-medium text-primary">
                        {reference.metadata.title}
                    </DialogDescription>
                </DialogHeader>

                <ScrollArea className="flex-1 mt-4 p-4 border rounded-md bg-muted/20">
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">
                        {reference.text}
                    </div>
                </ScrollArea>

                <div className="mt-2 text-xs text-muted-foreground flex justify-between">
                    <span>Score: {reference.score ? (reference.score * 100).toFixed(1) + '%' : 'N/A'}</span>
                    <span>Source: {reference.metadata.source || 'Official Text'}</span>
                </div>
            </DialogContent>
        </Dialog>
    );
}
