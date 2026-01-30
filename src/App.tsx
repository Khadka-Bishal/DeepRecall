import { useState, Suspense, lazy } from 'react';
import { LandingPage } from './components/LandingPage';
import { AnimatePresence, motion } from 'framer-motion';
import { ToastProvider } from './contexts/ToastContext';
import { DeepRecallLogo } from './components/DeepRecallLogo';

// Lazy load the main application
const DeepRecallApp = lazy(() => import('./DeepRecallApp'));

const LoadingScreen = () => (
  <div className="h-screen w-full flex flex-col items-center justify-center bg-[#09090b] text-zinc-500 gap-4">
    <div className="animate-pulse">
                  <DeepRecallLogo />
                </div>
    <div className="text-xs font-mono">Loading application...</div>
    </div>
  );

const App = () => {
  const [showLanding, setShowLanding] = useState(true);

  return (
    <ToastProvider>
      <AnimatePresence mode="wait">
        {showLanding ? (
          <motion.div
            key="landing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
          >
            <LandingPage onLaunch={() => setShowLanding(false)} />
          </motion.div>
        ) : (
          <motion.div
            key="app"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="h-screen" // Ensure full height for app
          >
            <DeepRecallApp onHome={() => setShowLanding(true)} />
          </motion.div>
        )}
      </AnimatePresence>
    </ToastProvider>
  );
};

export default App;
