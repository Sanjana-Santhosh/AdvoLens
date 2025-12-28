'use client';
import { useState, useRef } from 'react';
import { createIssue } from '@/lib/api';
import { Camera, MapPin, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function ReportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [location, setLocation] = useState<{lat: number, lon: number} | null>(null);
  const [loading, setLoading] = useState(false);
  const [description, setDescription] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Get Location
  const getLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLocation({ lat: pos.coords.latitude, lon: pos.coords.longitude });
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Unable to get location. Please enable location services.');
        }
      );
    } else {
      alert('Geolocation is not supported by your browser.');
    }
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
      alert(`Reported! ID: ${res.id}\nCaption: ${res.caption}\nTags: ${res.tags?.join(', ') || 'None'}`);
      // Reset form
      setFile(null);
      setLocation(null);
      setDescription('');
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
