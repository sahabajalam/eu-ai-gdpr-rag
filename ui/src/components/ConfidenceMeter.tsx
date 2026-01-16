
interface ConfidenceMeterProps {
    score: number; // 0 to 100
}

export function ConfidenceMeter({ score }: ConfidenceMeterProps) {
    let color = "bg-red-500";
    if (score >= 80) color = "bg-green-500";
    else if (score >= 60) color = "bg-yellow-500";

    return (
        <div className="flex items-center gap-2 group relative">
            <div className="text-xs font-semibold text-muted-foreground">
                Confidence: {score}%
            </div>
            <div className="h-2 w-24 bg-secondary rounded-full overflow-hidden">
                <div
                    className={`h-full ${color} transition-all duration-500`}
                    style={{ width: `${score}%` }}
                />
            </div>
        </div>
    );
}
