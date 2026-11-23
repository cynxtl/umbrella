import React, { useState, useEffect, useRef } from 'react';
import { MapPin, ChevronDown, Search, X, Check, Loader2 } from 'lucide-react';
import { LocationItem } from '../types';

interface LocationIndicatorProps {
  currentLocation: LocationItem | null;
  onSelectLocation: (location: LocationItem) => void;
}

export const LocationIndicator: React.FC<LocationIndicatorProps> = ({
  currentLocation,
  onSelectLocation,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<LocationItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close on click outside or Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };

    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.addEventListener('mousedown', handleClickOutside);
      // Auto-focus input when opened
      setTimeout(() => inputRef.current?.focus(), 50);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Load initial popular cities or search
  useEffect(() => {
    if (!isOpen) return;

    const query = searchQuery.trim();
    if (!query) {
      // Default initial suggestions
      fetch('/api/weather/geocode?query=India')
        .then((res) => (res.ok ? res.json() : []))
        .then((data) => setResults(data))
        .catch(() => setResults([]));
      return;
    }

    setIsSearching(true);
    const timer = setTimeout(() => {
      fetch(`/api/weather/geocode?query=${encodeURIComponent(query)}`)
        .then((res) => (res.ok ? res.json() : []))
        .then((data) => {
          setResults(data);
          setIsSearching(false);
        })
        .catch(() => {
          setResults([]);
          setIsSearching(false);
        });
    }, 200);

    return () => clearTimeout(timer);
  }, [searchQuery, isOpen]);

  const handleSelect = (item: LocationItem) => {
    onSelectLocation(item);
    setIsOpen(false);
    setSearchQuery('');
  };

  const isCurrent = (item: LocationItem) => {
    if (!currentLocation) return false;
    return (
      currentLocation.name.toLowerCase() === item.name.toLowerCase() &&
      (currentLocation.region || '').toLowerCase() === (item.region || '').toLowerCase() &&
      currentLocation.country.toLowerCase() === item.country.toLowerCase()
    );
  };

  const displayText = currentLocation
    ? currentLocation.display_name || `${currentLocation.name}, ${currentLocation.region ? currentLocation.region + ', ' : ''}${currentLocation.country}`
    : 'Choose location';

  return (
    <div className="relative inline-block text-left" ref={popoverRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.12] bg-white/[0.04] px-3 py-1 text-xs text-white hover:bg-white/[0.08] hover:border-white/[0.22] transition-colors focus:outline-none focus:ring-1 focus:ring-white/40"
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        title={displayText}
      >
        <MapPin className="h-3.5 w-3.5 text-text-secondary shrink-0" />
        <span className="max-w-[130px] xs:max-w-[180px] sm:max-w-[240px] md:max-w-[320px] truncate font-normal">
          {displayText}
        </span>
        <ChevronDown
          className={`h-3 w-3 text-text-muted transition-transform shrink-0 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-[300px] sm:w-[360px] rounded-2xl border border-white/[0.12] bg-[#0A0A0A] p-3.5 shadow-2xl backdrop-blur-xl z-50 animate-in fade-in zoom-in-95 duration-100">
          <div className="flex items-center justify-between pb-2.5 mb-2.5 border-b border-white/[0.08]">
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-white" />
              <span className="text-xs font-semibold text-white tracking-wide">
                Select Location
              </span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="rounded-md p-1 text-text-muted hover:text-white hover:bg-white/[0.06] transition-colors"
              title="Cancel"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="relative mb-2.5">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-text-muted" />
            <input
              ref={inputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search city, region, or country..."
              className="w-full rounded-xl border border-white/[0.10] bg-black/60 pl-8 pr-3 py-2 text-xs text-white placeholder:text-text-muted focus:outline-none focus:border-white/30 transition-colors"
            />
            {isSearching && (
              <Loader2 className="absolute right-2.5 top-2.5 h-3.5 w-3.5 animate-spin text-text-muted" />
            )}
          </div>

          <div className="max-h-[220px] overflow-y-auto space-y-1 pr-1 custom-scrollbar">
            {results.length > 0 ? (
              results.map((loc, idx) => {
                const active = isCurrent(loc);
                return (
                  <button
                    key={`${loc.name}-${loc.region}-${loc.country}-${idx}`}
                    onClick={() => handleSelect(loc)}
                    className={`w-full flex items-center justify-between rounded-lg px-2.5 py-2 text-left text-xs transition-colors ${
                      active
                        ? 'bg-white/[0.10] text-white'
                        : 'text-text-secondary hover:bg-white/[0.05] hover:text-white'
                    }`}
                  >
                    <div className="min-w-0 pr-2">
                      <div className="font-medium text-white truncate">
                        {loc.name}
                      </div>
                      <div className="text-[11px] text-text-muted truncate mt-0.5">
                        {loc.region ? `${loc.region}, ` : ''}
                        {loc.country}
                      </div>
                    </div>
                    {active && (
                      <Check className="h-3.5 w-3.5 text-white shrink-0" />
                    )}
                  </button>
                );
              })
            ) : isSearching ? (
              <div className="py-6 text-center text-xs text-text-muted">
                Resolving locations...
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-text-muted">
                No matching cities found.
              </div>
            )}
          </div>

          <div className="pt-2 mt-2 border-t border-white/[0.06] flex justify-between items-center text-[11px] text-text-muted">
            <span>Geocoded resolution</span>
            <button
              onClick={() => setIsOpen(false)}
              className="hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
