import { Cpu, Database, Github, ScanEye, GitMerge, Infinity, Workflow, UploadCloud } from 'lucide-react';
import { motion, Variants } from 'framer-motion';
import { DeepRecallLogo } from './DeepRecallLogo';

// Animation Variants
const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 15,
    },
  },
};

interface LandingPageProps {
  onLaunch: () => void;
}

export const LandingPage = ({ onLaunch }: LandingPageProps) => {
  return (
    <div className="min-h-screen bg-[#050505] text-zinc-100 selection:bg-emerald-500/30 selection:text-emerald-200 overflow-x-hidden font-sans">
      {/* Subtle Grid Background */}
      <div className="fixed inset-0 z-0 opacity-20 pointer-events-none" 
           style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, #333 1px, transparent 0)', backgroundSize: '40px 40px' }}>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8">
        
        {/* Navigation */}
        <nav className="flex items-center justify-between py-8">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => window.location.reload()}
          >
            <DeepRecallLogo />
            <span className="font-grotesk font-semibold text-lg tracking-tight group-hover:text-emerald-400 transition-colors">DeepRecall</span>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-6"
          >
            <a href="https://github.com/Khadka-Bishal/DeepRecall" target="_blank" rel="noreferrer" 
               className="flex items-center gap-2 text-sm text-zinc-400 hover:text-white transition-colors font-medium">
              <Github size={18} />
              <span>Source</span>
            </a>
            <button 
              onClick={onLaunch}
              className="px-5 py-2 text-sm font-medium bg-zinc-100 text-black rounded-full hover:bg-zinc-200 transition-all font-grotesk"
            >
              Launch Console
            </button>
          </motion.div>
        </nav>

        {/* Hero Section */}
        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="py-16 lg:py-24 flex flex-col items-start max-w-4xl"
        >
          <motion.div variants={itemVariants} className="flex items-center gap-2 mb-6">
             <span className="px-2 py-1 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-mono">
              Serverless v2.0
            </span>
            <span className="px-2 py-1 rounded bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs font-mono">
              Open Source
            </span>
          </motion.div>

          <motion.h1 
            variants={itemVariants}
            className="text-4xl sm:text-5xl lg:text-7xl font-bold tracking-tight text-white mb-6 font-grotesk leading-[1.1]"
          >
            Trust your AI <br/>
            <span className="text-zinc-500">with Transparent Retrieval.</span>
          </motion.h1>

          <motion.p 
            variants={itemVariants}
            className="text-lg text-zinc-400 max-w-2xl mb-10 leading-relaxed"
          >
            Stop hallucinations. We show you exactly which chunks were retrieved for every answer.
          </motion.p>
        </motion.div>

        {/* Architecture Diagram */}
        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="py-12 border-t border-zinc-900"
        >
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-12">
            <div>
              <h2 className="text-3xl font-bold text-white mb-2 font-grotesk">Cloud Architecture</h2>
              <p className="text-zinc-500">Efficient. Scalable.</p>
            </div>
          </div>

          <div className="relative rounded-xl border border-zinc-800 bg-[#0A0A0A] p-8 lg:p-12 overflow-hidden">
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
            
            {/* Detailed Flow Diagram */}
            <div className="relative flex flex-col lg:flex-row items-center justify-between gap-8 lg:gap-4 z-10 w-full">
               
               <motion.div 
                 whileHover={{ scale: 1.05 }}
                 className="flex flex-col items-center text-center gap-4 relative z-10 group"
               >
                  <div className="w-14 h-14 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center shadow-2xl group-hover:border-zinc-700 transition-colors">
                     <UploadCloud size={22} className="text-zinc-100" />
                  </div>
                  <div className="text-xs font-mono text-zinc-500 pt-2">Client Upload</div>
               </motion.div>

               <div className="h-8 w-[2px] lg:w-full lg:h-[2px] bg-zinc-800 lg:flex-1 relative"></div>

               {/* Step 1: Storage */}
               <motion.div 
                 whileHover={{ scale: 1.05 }}
                 className="flex flex-col items-center text-center gap-4 relative z-10 group"
               >
                  <div className="w-14 h-14 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center shadow-2xl group-hover:border-blue-500/50 transition-colors">
                     {/* Using Database as generic bucket, styled orange for S3 feel */}
                     <Database size={22} className="text-orange-500" />
                  </div>
                  <div className="text-xs font-mono text-zinc-500 pt-2">S3 Bucket</div>
               </motion.div>

               <div className="h-8 w-[2px] lg:w-full lg:h-[2px] bg-zinc-800 lg:flex-1 relative"></div>

               {/* Step 2: Orchestration */}
               <motion.div 
                 whileHover={{ scale: 1.05 }}
                 className="flex flex-col items-center text-center gap-4 relative z-10 group"
               >
                  <div className="w-14 h-14 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center shadow-2xl ring-1 ring-orange-500/20 bg-orange-500/5 group-hover:bg-orange-500/10 transition-colors">
                     <Workflow size={22} className="text-orange-500" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-zinc-300">Step Functions</div>
                    <div className="text-[10px] font-mono text-zinc-500 mt-0.5">Orchestrator</div>
                  </div>
               </motion.div>

                <div className="h-8 w-[2px] lg:w-full lg:h-[2px] bg-zinc-800 lg:flex-1 relative"></div>

               {/* Step 3: Compute */}
                <motion.div 
                  whileHover={{ scale: 1.05 }}
                  className="flex flex-col items-center text-center gap-4 relative z-10 group"
                >
                  <div className="w-14 h-14 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center shadow-2xl group-hover:border-amber-500/50 transition-colors">
                     <Cpu size={22} className="text-amber-400" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-zinc-300">Lambda</div>
                    <div className="text-[10px] font-mono text-zinc-500 mt-0.5">ADE Processing</div>
                  </div>
               </motion.div>

                <div className="h-8 w-[2px] lg:w-full lg:h-[2px] bg-zinc-800 lg:flex-1 relative"></div>

               {/* Step 4: Knowledge */}
                <motion.div 
                  whileHover={{ scale: 1.05 }}
                  className="flex flex-col items-center text-center gap-4 relative z-10 group"
                >
                  <div className="w-14 h-14 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center shadow-2xl group-hover:border-pink-500/50 transition-colors">
                     <Database size={22} className="text-pink-400" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-zinc-300">Pinecone</div>
                    <div className="text-[10px] font-mono text-zinc-500 mt-0.5">Serverless Index</div>
                  </div>
               </motion.div>

                <div className="h-8 w-[2px] lg:w-full lg:h-[2px] bg-zinc-800 lg:flex-1 relative"></div>

               {/* Step 5: Search */}
               <motion.div 
                 whileHover={{ scale: 1.05 }}
                 className="flex flex-col items-center text-center gap-4 relative z-10 group"
               >
                  <div className="w-14 h-14 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center shadow-2xl group-hover:border-emerald-500/50 transition-colors cursor-help">
                     <ScanEye size={22} className="text-emerald-400" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-zinc-300">Grounded RAG</div>
                    <div className="text-[10px] font-mono text-zinc-500 mt-0.5">Visual Verify</div>
                  </div>
               </motion.div>
            </div>
          </div>
        </motion.div>

        {/* Deep Dive Grid */}
        <div className="py-20 border-t border-zinc-900">
           <div className="mb-16">
              <h2 className="text-3xl font-bold text-white mb-2 font-grotesk">Core Capabilities</h2>
           </div>

           <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
               <div className="p-6 rounded-xl bg-zinc-900/20 border border-zinc-800 hover:border-zinc-700 transition-colors">
                  <div className="w-10 h-10 rounded bg-emerald-500/10 flex items-center justify-center mb-4">
                    <ScanEye size={20} className="text-emerald-500" />
                  </div>
                  <h3 className="text-lg font-bold text-zinc-100 mb-2 font-grotesk">Chunk Retrieval</h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    We map every answer to the original text chunks. Verify the truth instantly.
                  </p>
               </div>

               <div className="p-6 rounded-xl bg-zinc-900/20 border border-zinc-800 hover:border-zinc-700 transition-colors">
                  <div className="w-10 h-10 rounded bg-blue-500/10 flex items-center justify-center mb-4">
                    <GitMerge size={20} className="text-blue-500" />
                  </div>
                  <h3 className="text-lg font-bold text-zinc-100 mb-2 font-grotesk">Hybrid Search</h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    Combines Semantic Vector search with Keyword search (BM25) for better relevance.
                  </p>
               </div>

                <div className="p-6 rounded-xl bg-zinc-900/20 border border-zinc-800 hover:border-zinc-700 transition-colors">
                  <div className="w-10 h-10 rounded bg-amber-500/10 flex items-center justify-center mb-4">
                    <Infinity size={20} className="text-amber-500" />
                  </div>
                  <h3 className="text-lg font-bold text-zinc-100 mb-2 font-grotesk">Serverless</h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    Zero idle costs. Infinite scale. Powered by AWS Lambda.
                  </p>
               </div>
           </div>
        </div>
      </div>
    </div>
  );
};
