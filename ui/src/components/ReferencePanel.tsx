
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

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

interface ReferencePanelProps {
    references: Reference[];
    onSelectReference: (ref: Reference) => void;
}

export function ReferencePanel({ references, onSelectReference }: ReferencePanelProps) {
    if (!references || references.length === 0) {
        return (
            <div className="text-muted-foreground text-sm p-4 text-center">
                No references retrieved yet.
            </div>
        );
    }

    return (
        <ScrollArea className="h-full w-full pr-4">
            <div className="flex flex-col gap-4 p-1">
                {references.map((ref, idx) => (
                    <Card
                        key={idx}
                        className="bg-card/50 cursor-pointer hover:bg-muted/50 transition-colors"
                        onClick={() => onSelectReference(ref)}
                    >
                        <CardHeader className="p-3 pb-1">
                            <CardTitle className="text-sm font-bold text-primary">
                                {ref.metadata.regulation} Art. {ref.metadata.article_number}
                            </CardTitle>
                            <div className="text-xs text-muted-foreground font-medium">
                                {ref.metadata.title}
                            </div>
                        </CardHeader>
                        <CardContent className="p-3 pt-2">
                            <p className="text-xs text-muted-foreground line-clamp-4 leading-relaxed">
                                {ref.text}
                            </p>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </ScrollArea>
    );
}
