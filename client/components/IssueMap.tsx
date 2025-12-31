'use client';

import { useEffect, useRef, useState } from 'react';

// Type for Leaflet Map (will be loaded dynamically)
type LeafletMap = {
  setView: (center: [number, number], zoom: number) => LeafletMap;
  fitBounds: (bounds: [number, number][], options?: { padding?: [number, number]; maxZoom?: number }) => LeafletMap;
  remove: () => void;
};

interface Issue {
  id: number;
  caption?: string | null;
  tags?: string[] | null;
  status: string;
  lat?: number | null;
  lon?: number | null;
  image_url?: string;
  department?: string | null;
}

interface Hotspot {
  cluster_id: number;
  center: { lat: number; lon: number };
  issue_count: number;
  issue_ids: number[];
  primary_department?: string;
}

interface IssueMapProps {
  issues: Issue[];
  hotspots?: Hotspot[];
  center?: [number, number]; // [lat, lon]
  zoom?: number;
  height?: string;
  showHotspots?: boolean;
}

// Status colors
const statusColors: Record<string, string> = {
  'Open': '#ef4444',        // red
  'In Progress': '#f59e0b', // amber
  'Resolved': '#22c55e',    // green
};

export default function IssueMap({ 
  issues, 
  hotspots = [], 
  center = [8.5241, 76.9366], // Default: Trivandrum, Kerala [lat, lon]
  zoom = 12,
  height = '100%',
  showHotspots = true
}: IssueMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<LeafletMap | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Only run on client
    if (typeof window === 'undefined') return;

    // Dynamically import Leaflet
    const initMap = async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const L = (await import('leaflet' as any)).default as any;
      
      // Fix default marker icons
      delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
      });

      if (!mapRef.current || mapInstanceRef.current) return;

      // Filter valid issues
      const validIssues = issues.filter(i => i.lat != null && i.lon != null);
      
      // Calculate initial center
      let mapCenter: [number, number] = center;
      if (validIssues.length > 0) {
        const avgLat = validIssues.reduce((sum, i) => sum + (i.lat || 0), 0) / validIssues.length;
        const avgLon = validIssues.reduce((sum, i) => sum + (i.lon || 0), 0) / validIssues.length;
        mapCenter = [avgLat, avgLon];
      }

      // Initialize map
      const map = L.map(mapRef.current).setView(mapCenter, zoom);
      mapInstanceRef.current = map;

      // Add OpenStreetMap tiles
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);

      // Create colored marker icon
      const createMarkerIcon = (color: string) => {
        return L.divIcon({
          className: 'custom-marker',
          html: `
            <div style="
              width: 24px;
              height: 24px;
              background: ${color};
              border: 3px solid white;
              border-radius: 50%;
              box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            "></div>
          `,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
          popupAnchor: [0, -12],
        });
      };

      // Create hotspot marker icon
      const createHotspotIcon = (count: number) => {
        const size = Math.min(40 + count * 4, 80);
        return L.divIcon({
          className: 'hotspot-marker',
          html: `
            <div style="
              width: ${size}px;
              height: ${size}px;
              background: rgba(245, 158, 11, 0.4);
              border: 3px solid #f59e0b;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              font-weight: bold;
              color: #b45309;
              font-size: 14px;
              animation: pulse 2s infinite;
            ">
              🔥${count}
            </div>
          `,
          iconSize: [size, size],
          iconAnchor: [size / 2, size / 2],
          popupAnchor: [0, -size / 2],
        });
      };

      // Add issue markers
      const bounds: [number, number][] = [];
      validIssues.forEach((issue) => {
        const lat = issue.lat as number;
        const lon = issue.lon as number;
        const color = statusColors[issue.status] || '#6b7280';
        
        bounds.push([lat, lon]);
        
        const statusClass = 
          issue.status === 'Open' ? 'bg-red-100 text-red-700' :
          issue.status === 'In Progress' ? 'bg-amber-100 text-amber-700' :
          'bg-green-100 text-green-700';
        
        const popupContent = `
          <div class="p-1" style="min-width: 200px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
              <span style="font-weight: bold; font-size: 14px;">Issue #${issue.id}</span>
              <span class="${statusClass}" style="font-size: 12px; padding: 2px 8px; border-radius: 9999px;">${issue.status}</span>
            </div>
            ${issue.image_url ? `<img src="${issue.image_url}" style="width: 100%; height: 96px; object-fit: cover; border-radius: 4px; margin-bottom: 8px;" />` : ''}
            <p style="font-size: 12px; color: #666; margin-bottom: 8px;">${issue.caption || 'No description'}</p>
            ${issue.tags && issue.tags.length > 0 ? `
              <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px;">
                ${issue.tags.slice(0, 3).map(tag => `<span style="font-size: 12px; background: #f3f4f6; padding: 2px 8px; border-radius: 4px;">${tag}</span>`).join('')}
              </div>
            ` : ''}
            ${issue.department ? `<p style="font-size: 12px; color: #2563eb; font-weight: 500;">📋 ${issue.department.replace('_', ' ')}</p>` : ''}
          </div>
        `;
        
        L.marker([lat, lon], { icon: createMarkerIcon(color) })
          .addTo(map)
          .bindPopup(popupContent, { maxWidth: 280 });
      });

      // Add hotspot markers and circles
      if (showHotspots) {
        hotspots.forEach((hotspot) => {
          bounds.push([hotspot.center.lat, hotspot.center.lon]);
          
          // Hotspot marker
          const popupContent = `
            <div style="padding: 8px;">
              <h3 style="font-weight: bold; color: #d97706; margin-bottom: 4px;">🔥 Problem Hotspot</h3>
              <p style="font-size: 14px; font-weight: 500;">${hotspot.issue_count} issues in this area</p>
              ${hotspot.primary_department ? `<p style="font-size: 12px; color: #666; margin-top: 4px;">Primary: ${hotspot.primary_department.replace('_', ' ')}</p>` : ''}
              <p style="font-size: 12px; color: #888; margin-top: 8px;">
                Issue IDs: ${hotspot.issue_ids.slice(0, 5).join(', ')}${hotspot.issue_ids.length > 5 ? '...' : ''}
              </p>
            </div>
          `;
          
          L.marker([hotspot.center.lat, hotspot.center.lon], { icon: createHotspotIcon(hotspot.issue_count) })
            .addTo(map)
            .bindPopup(popupContent);
          
          // Hotspot circle
          L.circle([hotspot.center.lat, hotspot.center.lon], {
            radius: 100,
            color: '#f59e0b',
            fillColor: '#fbbf24',
            fillOpacity: 0.2,
            weight: 2,
          }).addTo(map);
        });
      }

      // Fit bounds
      if (bounds.length > 1) {
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
      }

      setIsLoaded(true);
    };

    initMap();

    // Cleanup
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [issues, hotspots, center, zoom, showHotspots]);

  return (
    <>
      <style jsx global>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.1); opacity: 0.8; }
        }
        .custom-marker, .hotspot-marker {
          background: transparent !important;
          border: none !important;
        }
        .leaflet-popup-content-wrapper {
          border-radius: 8px;
        }
      `}</style>
      <div 
        ref={mapRef}
        className="w-full rounded-lg"
        style={{ height, minHeight: '300px' }}
      >
        {!isLoaded && (
          <div className="flex items-center justify-center h-full bg-gray-100 rounded-lg animate-pulse">
            <p className="text-gray-500">🗺️ Loading map...</p>
          </div>
        )}
      </div>
    </>
  );
}
