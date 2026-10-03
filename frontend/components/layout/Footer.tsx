'use client';

export function Footer() {
  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">
              About Prelegal
            </h3>
            <p className="text-sm text-gray-600">
              A platform for drafting common legal agreements quickly and easily.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">
              Legal
            </h3>
            <p className="text-sm text-gray-600">
              Generated documents are provided as-is. Consult with a lawyer before signing.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">
              Attribution
            </h3>
            <p className="text-sm text-gray-600">
              Templates from CommonPaper under CC BY 4.0
            </p>
          </div>
        </div>
        <div className="border-t border-gray-200 mt-8 pt-8 text-center text-sm text-gray-600">
          <p>&copy; 2024 Prelegal. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
