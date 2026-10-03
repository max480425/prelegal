'use client';

export function Header() {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Prelegal</h1>
            <p className="text-sm text-gray-600">NDA Creator</p>
          </div>
          <div className="text-sm text-gray-600">
            Create Mutual NDA Documents
          </div>
        </div>
      </div>
    </header>
  );
}
