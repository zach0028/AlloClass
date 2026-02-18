export function confidenceTextColor(confidence: number): string {
  if (confidence >= 0.85) return "text-green-600";
  if (confidence >= 0.7) return "text-yellow-600";
  return "text-red-600";
}

export function confidenceBarColor(confidence: number): string {
  if (confidence >= 0.85) return "bg-green-500";
  if (confidence >= 0.7) return "bg-yellow-500";
  return "bg-red-500";
}
