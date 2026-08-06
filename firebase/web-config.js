// Firebase Web SDK configuration — these identifiers are public by design.
// Security must be enforced with Authentication, Firestore Rules and API-key restrictions.
import { initializeApp, getApps } from "firebase/app";

export const firebaseConfig = {
  apiKey: "AIzaSyDOLzhPbmXdIqN4U4sjwwDXrzMDhKWeLL8",
  authDomain: "studio-189872345-78684.firebaseapp.com",
  projectId: "studio-189872345-78684",
  storageBucket: "studio-189872345-78684.firebasestorage.app",
  messagingSenderId: "950478899811",
  appId: "1:950478899811:web:d05edd959937f53d560656"
};

export const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);
