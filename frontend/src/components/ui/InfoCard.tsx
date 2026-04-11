/**
 * Carte d'information avec titre, description et contenu.
 * Utilisée pour expliquer chaque section aux débutants.
 */

import { useState } from "react";
import { ChevronDown, ChevronUp, Info } from "lucide-react";

interface Props {
  title: string;
  description: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
  defaultExpanded?: boolean;
  accentColor?: string;
}

export default function InfoCard({
  title,
  description,
  children,
  icon,
  defaultExpanded = true,
  accentColor = "#D4AF37",
}: Props) {
  const [showInfo, setShowInfo] = useState(false);

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-border/50">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {icon && (
              <div
                className="w-9 h-9 rounded-lg flex items-center justify-center text-sm"
                style={{ background: `${accentColor}15`, color: accentColor }}
              >
                {icon}
              </div>
            )}
            <div>
              <h3 className="text-sm font-semibold">{title}</h3>
              <button
                onClick={() => setShowInfo(!showInfo)}
                className="flex items-center gap-1 text-[11px] text-text-secondary hover:text-gold transition-colors mt-0.5"
              >
                <Info size={11} />
                {showInfo ? "Masquer l'explication" : "Comment lire cette section ?"}
              </button>
            </div>
          </div>
        </div>

        {/* Description pédagogique */}
        {showInfo && (
          <div
            className="mt-3 p-3 rounded-lg text-xs leading-relaxed text-text-secondary"
            style={{ background: `${accentColor}08`, borderLeft: `3px solid ${accentColor}40` }}
          >
            {description}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-5">{children}</div>
    </div>
  );
}
