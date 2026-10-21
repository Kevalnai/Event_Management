import { Route, Routes } from "react-router-dom";
import Layout from "./components/layout/Layout";
import ProtectedRoute from "./components/layout/ProtectedRoute";
import Home from "./pages/Home";
import Events from "./pages/Events";
import EventDetail from "./pages/EventDetail";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Checkout from "./pages/Checkout";
import CheckoutSuccess from "./pages/CheckoutSuccess";
import Dashboard from "./pages/Dashboard";
import Profile from "./pages/Profile";
import CreateEvent from "./pages/CreateEvent";
import ManageEvent from "./pages/ManageEvent";
import Scanner from "./pages/Scanner";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/events" element={<Events />} />
        <Route path="/events/:id" element={<EventDetail />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        <Route
          path="/create-event"
          element={
            <ProtectedRoute>
              <CreateEvent />
            </ProtectedRoute>
          }
        />
        <Route
          path="/checkout/:registrationId"
          element={
            <ProtectedRoute>
              <Checkout />
            </ProtectedRoute>
          }
        />
        <Route
          path="/checkout/:registrationId/success"
          element={
            <ProtectedRoute>
              <CheckoutSuccess />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/events/:eventId/manage"
          element={
            <ProtectedRoute>
              <ManageEvent />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/scanner"
          element={
            <ProtectedRoute>
              <Scanner />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
