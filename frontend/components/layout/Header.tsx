'use client';

import Link from 'next/link';
import { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';

export function Header() {
  const { user, isLoading, signout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close the user menu on outside click
  useEffect(() => {
    if (!menuOpen) return;
    const onClick = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, [menuOpen]);

  const handleSignout = async () => {
    setMenuOpen(false);
    await signout();
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="block">
            <h1 className="text-2xl font-bold text-[#032147]">Prelegal</h1>
            <p className="text-sm text-gray-600">NDA Creator</p>
          </Link>

          <div className="flex items-center gap-4">
            {isLoading ? null : user ? (
              <div className="relative" ref={menuRef}>
                <button
                  type="button"
                  onClick={() => setMenuOpen((open) => !open)}
                  className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 font-medium px-3 py-2 rounded-lg hover:bg-gray-50"
                  aria-haspopup="menu"
                  aria-expanded={menuOpen}
                >
                  {/* Simple avatar with initial */}
                  <span className="w-8 h-8 rounded-full bg-[#209dd7] text-white flex items-center justify-center text-sm font-bold">
                    {user.email.charAt(0).toUpperCase()}
                  </span>
                  <span className="hidden sm:inline max-w-[160px] truncate">
                    {user.email}
                  </span>
                </button>

                {menuOpen && (
                  <div
                    role="menu"
                    className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50"
                  >
                    <div className="px-4 py-2 text-xs text-gray-500 border-b border-gray-100 truncate">
                      {user.email}
                    </div>
                    <button
                      type="button"
                      onClick={handleSignout}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      role="menuitem"
                    >
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <>
                <Link
                  href="/signin/"
                  className="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2"
                >
                  Sign in
                </Link>
                <Link
                  href="/signin/?mode=signup"
                  className="text-sm font-medium text-white bg-[#753991] hover:bg-[#5f2f7a] px-4 py-2 rounded-lg"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
