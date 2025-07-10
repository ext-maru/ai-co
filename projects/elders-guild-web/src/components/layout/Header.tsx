'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Moon, Sun, Menu, X, Activity, Users, Terminal, Settings } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Avatar, AvatarFallback } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { useSageStore } from '@/stores/sageStore'

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { theme, toggleTheme, culturalMode, toggleCulturalMode, hierarchy, getActiveSages } = useSageStore()
  const activeSages = getActiveSages()

  return (
    <header className="sticky top-0 z-50 w-full border-b border-sage-200 bg-white/80 backdrop-blur-md dark:border-sage-800 dark:bg-sage-950/80">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center gap-4">
            <motion.div
              initial={{ rotate: 0 }}
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="relative"
            >
              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-elder-600 to-elder-700 p-2 shadow-elder">
                <Terminal className="h-full w-full text-white" />
              </div>
            </motion.div>
            <div>
              <h1 className="text-xl font-bold text-sage-900 dark:text-sage-50">
                AI Company {culturalMode ? '道場' : 'Dojo'}
              </h1>
              <p className="text-xs text-sage-600 dark:text-sage-400">
                {culturalMode ? '四賢者システム' : '4 Sages System'}
              </p>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-green-600" />
              <span className="text-sm font-medium">
                {culturalMode ? '稼働中' : 'Active'}: {activeSages.length}/4
              </span>
            </div>
            
            <Badge variant="elder" size="lg" className="gap-2">
              <Users className="h-4 w-4" />
              {hierarchy.name}
            </Badge>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleCulturalMode}
                title={culturalMode ? 'Switch to English' : '日本語に切り替え'}
              >
                <span className="text-lg">{culturalMode ? '和' : 'EN'}</span>
              </Button>
              
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                title={theme === 'light' ? 'Dark mode' : 'Light mode'}
              >
                {theme === 'light' ? (
                  <Moon className="h-5 w-5" />
                ) : (
                  <Sun className="h-5 w-5" />
                )}
              </Button>

              <Button variant="ghost" size="icon">
                <Settings className="h-5 w-5" />
              </Button>

              <Avatar sage="elder" size="default">
                <AvatarFallback>
                  <span className="text-sm font-bold">GM</span>
                </AvatarFallback>
              </Avatar>
            </div>
          </nav>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </Button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <motion.nav
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-4 flex flex-col gap-3 border-t border-sage-200 pt-4 dark:border-sage-800 md:hidden"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium">
                  {culturalMode ? '稼働中' : 'Active'}: {activeSages.length}/4
                </span>
              </div>
              <Badge variant="elder" size="sm">
                {hierarchy.level}
              </Badge>
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={toggleCulturalMode}
                className="flex-1"
              >
                {culturalMode ? 'English Mode' : '日本語モード'}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={toggleTheme}
                className="flex-1"
              >
                {theme === 'light' ? 'Dark' : 'Light'}
              </Button>
            </div>
          </motion.nav>
        )}
      </div>
    </header>
  )
}