export default function LoadingScreen({ message = "Chargement..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64">
      <div className="relative w-16 h-16 mb-6">
        {/* Anneau extérieur */}
        <div className="absolute inset-0 rounded-full border-2 border-border" />
        {/* Anneau animé */}
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-gold animate-spin" />
        {/* Point central */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-2 h-2 rounded-full bg-gold animate-pulse" />
        </div>
      </div>
      <p className="text-text-secondary text-sm">{message}</p>
    </div>
  );
}
