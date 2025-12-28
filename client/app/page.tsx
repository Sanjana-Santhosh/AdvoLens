import Link from "next/link";
import { MapPin, Camera, Users, Shield, Settings } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <header className="px-4 py-6">
        <div className="max-w-md mx-auto lg:max-w-6xl flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
              <MapPin className="text-white" size={24} />
            </div>
            <span className="text-xl font-bold text-gray-800">AdvoLens</span>
          </div>
          <Link
            href="/admin/dashboard"
            className="flex items-center text-gray-600 hover:text-blue-600 text-sm"
          >
            <Settings size={18} className="mr-1" />
            <span className="hidden sm:inline">Admin</span>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="px-4 py-8">
        <div className="max-w-md mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Report Issues.
            <br />
            <span className="text-blue-600">Improve Your City.</span>
          </h1>
          <p className="text-gray-600 mb-8">
            Use AI-powered reporting to identify and track civic issues in your community. 
            Together, we can make a difference.
          </p>

          {/* Action Buttons */}
          <div className="space-y-4 mb-12">
            <Link
              href="/report"
              className="flex items-center justify-center w-full bg-blue-600 text-white p-4 rounded-xl font-bold hover:bg-blue-700 transition-colors shadow-lg shadow-blue-200"
            >
              <Camera className="mr-2" size={24} />
              Report an Issue
            </Link>
            <Link
              href="/feed"
              className="flex items-center justify-center w-full bg-white text-gray-800 p-4 rounded-xl font-bold hover:bg-gray-50 transition-colors border border-gray-200"
            >
              <Users className="mr-2" size={24} />
              View Community Reports
            </Link>
          </div>

          {/* Features */}
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-gray-800">How it works</h2>
            
            <div className="grid gap-4">
              <div className="bg-white rounded-xl p-4 border border-gray-100 flex items-start space-x-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Camera className="text-blue-600" size={24} />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800">Take a Photo</h3>
                  <p className="text-sm text-gray-500">Snap a picture of the civic issue you spot</p>
                </div>
              </div>

              <div className="bg-white rounded-xl p-4 border border-gray-100 flex items-start space-x-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <MapPin className="text-green-600" size={24} />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800">Share Location</h3>
                  <p className="text-sm text-gray-500">GPS automatically pins the exact location</p>
                </div>
              </div>

              <div className="bg-white rounded-xl p-4 border border-gray-100 flex items-start space-x-4">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Shield className="text-purple-600" size={24} />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800">AI Analysis</h3>
                  <p className="text-sm text-gray-500">Our AI categorizes and prioritizes your report automatically</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-4 py-8 mt-8">
        <div className="max-w-md mx-auto text-center text-sm text-gray-400">
          <p>Built with ❤️ for better communities</p>
          <p className="mt-1">© 2025 AdvoLens</p>
        </div>
      </footer>
    </div>
  );
}
