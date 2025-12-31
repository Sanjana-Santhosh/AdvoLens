'use client';
import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createIssue } from '@/lib/api';
import { Camera, MapPin, ArrowLeft, AlertTriangle } from 'lucide-react';
import Link from 'next/link';

export default function ReportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [location, setLocation] = useState<{lat: number, lon: number} | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const [description, setDescription] = useState('');
  const [locationError, setLocationError] = useState<string | null>(null);
  const [manualLocation, setManualLocation] = useState(false);
  const [manualLat, setManualLat] = useState('');
  const [manualLon, setManualLon] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Check if geolocation is available on mount
  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser.');
    }
  }, []);

  // Get Location
  const getLocation = () => {
    setLocationError(null);
    
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser.');
      setManualLocation(true);
      return;
    }

    // Check if we're on a secure context
    if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
      setLocationError('Location access requires HTTPS or localhost. Please use manual entry.');
      setManualLocation(true);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({ lat: pos.coords.latitude, lon: pos.coords.longitude });
        setLocationError(null);
        setManualLocation(false);
      },
      (error) => {
        console.error('Error getting location:', error);
        let errorMessage = 'Unable to get location.';
        
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Location permission denied. Please enable it in your browser settings or use manual entry.';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Location information unavailable. Please try manual entry.';
            break;
          case error.TIMEOUT:
            errorMessage = 'Location request timed out. Please try again or use manual entry.';
            break;
        }
        
        setLocationError(errorMessage);
        setManualLocation(true);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  };

  // Handle manual location submission
  const handleManualLocationSubmit = () => {
    const lat = parseFloat(manualLat);
    const lon = parseFloat(manualLon);
    
    if (isNaN(lat) || isNaN(lon)) {
      alert('Please enter valid coordinates');
      return;
    }
    
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
      alert('Invalid coordinates. Latitude must be between -90 and 90, Longitude between -180 and 180.');
      return;
    }
    
    setLocation({ lat, lon });
    setLocationError(null);
  };

  // Handle Submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !location) {
      alert("Please add photo and location!");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('image', file);
    formData.append('lat', location.lat.toString());
    formData.append('lon', location.lon.toString());
    
    if (description) {
      formData.append('description', description);
    }

    try {
      const res = await createIssue(formData);
      
      // Save tracking token for notifications
      if (res.tracking_token) {
        localStorage.setItem('tracking_token', res.tracking_token);
      }
      
      // Show success message with department info
      const deptLabel = res.department?.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()) || 'Unknown';
      alert(`✅ Report Submitted!\n\nIssue ID: #${res.id}\nDepartment: ${deptLabel}\nCaption: ${res.caption}\nTags: ${res.tags?.join(', ') || 'None'}\n\nYour tracking token has been saved. Check "My Updates" to track progress!`);
      
      // Reset form
      setFile(null);
      setLocation(null);
      setDescription('');
      
      // Redirect to notifications page
      router.push('/notifications');
    } catch (err) {
      console.error(err);
      alert("Failed to report. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center">
        <Link href="/" className="mr-4">
          <ArrowLeft size={24} className="text-gray-600" />
        </Link>
        <h1 className="text-xl font-bold text-gray-800">Report an Issue</h1>
      </div>

      <div className="p-4 max-w-2xl mx-auto lg:py-8">
        <form onSubmit={handleSubmit} className="space-y-6 lg:grid lg:grid-cols-2 lg:gap-8 lg:space-y-0">
          
          {/* Left Column - Image */}
          <div className="lg:space-y-6">
            {/* Camera Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Photo *
              </label>
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-gray-300 rounded-xl h-48 lg:h-64 flex flex-col items-center justify-center cursor-pointer bg-white hover:bg-gray-50 transition-colors"
              >
                {file ? (
                  <img 
                    src={URL.createObjectURL(file)} 
                    alt="Preview"
                    className="h-full w-full object-cover rounded-xl" 
                  />
                ) : (
                  <>
                    <Camera size={40} className="text-gray-400 mb-2" />
                    <span className="text-gray-500">Tap to take photo</span>
                    <span className="text-xs text-gray-400 mt-1">or select from gallery</span>
                  </>
                )}
              </div>
              <input 
                type="file" 
                ref={fileInputRef} 
                hidden 
                accept="image/*" 
                capture="environment"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </div>
          </div>

          {/* Right Column - Details */}
          <div className="space-y-6">
            {/* Description (Optional) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description (Optional)
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add any additional details..."
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none text-gray-900 bg-white placeholder-gray-400"
                rows={3}
              />
            </div>

            {/* Location Button */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Location *
              </label>
              
              {/* Location Error Message */}
              {locationError && (
                <div className="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2 text-amber-800 text-sm">
                  <AlertTriangle size={18} className="flex-shrink-0 mt-0.5" />
                  <span>{locationError}</span>
                </div>
              )}
              
              {/* Get Location Button */}
              <button 
                type="button"
                onClick={getLocation}
                className={`flex items-center justify-center w-full p-3 rounded-lg border transition-colors ${
                  location 
                    ? 'bg-green-50 border-green-500 text-green-700' 
                    : 'bg-white border-gray-300 hover:bg-gray-50 text-gray-700'
                }`}
              >
                <MapPin size={20} className="mr-2" />
                {location ? (
                  <span>
                    Location Captured
                    <span className="text-xs block text-green-600">
                      {location.lat.toFixed(6)}, {location.lon.toFixed(6)}
                    </span>
                  </span>
                ) : (
                  "Get Current Location"
                )}
              </button>
              
              {/* Manual Location Entry */}
              {manualLocation && !location && (
                <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-600 mb-2">Enter coordinates manually:</p>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-gray-500">Latitude</label>
                      <input
                        type="number"
                        step="any"
                        placeholder="e.g. 10.0159"
                        value={manualLat}
                        onChange={(e) => setManualLat(e.target.value)}
                        className="w-full p-2 text-sm border border-gray-300 rounded bg-white text-gray-900 placeholder-gray-400"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Longitude</label>
                      <input
                        type="number"
                        step="any"
                        placeholder="e.g. 76.3419"
                        value={manualLon}
                        onChange={(e) => setManualLon(e.target.value)}
                        className="w-full p-2 text-sm border border-gray-300 rounded bg-white text-gray-900 placeholder-gray-400"
                      />
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleManualLocationSubmit}
                    className="mt-2 w-full p-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                  >
                    Set Location
                  </button>
                  <p className="text-xs text-gray-400 mt-2">
                    Tip: You can find coordinates from Google Maps by right-clicking on a location.
                  </p>
                </div>
              )}
              
              {/* Toggle manual entry link */}
              {!manualLocation && !location && (
                <button
                  type="button"
                  onClick={() => setManualLocation(true)}
                  className="mt-2 text-xs text-blue-600 hover:underline"
                >
                  Can&apos;t get location? Enter manually
                </button>
              )}
            </div>

            {/* Submit Button */}
            <button 
              type="submit" 
              disabled={loading || !file || !location}
              className="w-full bg-blue-600 text-white p-4 rounded-xl font-bold disabled:bg-gray-400 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analyzing Image...
                </span>
              ) : (
                "Submit Report"
              )}
            </button>
          </div>
        </form>

        {/* Help Text */}
        <p className="text-center text-xs text-gray-500 mt-6 lg:mt-8">
          Your report will be analyzed by AI to automatically categorize and prioritize the issue.
        </p>
      </div>
    </div>
  );
}
