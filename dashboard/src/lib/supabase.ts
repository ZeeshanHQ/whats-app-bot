import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://xlnznsblnkhwbykddwzw.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhsbnpuc2Jsbmtod2J5a2Rkd3p3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ2MDU3MjAsImV4cCI6MjEwMDE4MTcyMH0.1Roj_HGNzVTbo5QUYANpN0pXaLfoLXgMApobzX7-ZbY';

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
  },
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
  },
});
