import { useState } from "react";
import API from "../utils/api";
import { useNavigate } from "react-router-dom";


export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate= useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    console.log("An attempt was made to login for the user", email)
    try {
      const response = await API.post('/login', {
        email,
        password
      })
      const { token } = response.data;
      const userId = response.data.userId;
      localStorage.setItem('authToken', token);
      localStorage.setItem('userId',userId)
      console.log("Set user Id",userId);
      navigate('/chat')
    } catch (e) {
      console.error("Login failed.", e)
      alert('Login Failed. Please re-validate your credentials.');
    }

  };

  return (
    <div className="grid grid-cols-3 min-h-screen bg-black-100 relative">
      {/* Left gear */}
      <div className="flex items-start justify-start px-4">
        <img src="/gears.svg" alt="Gear Left" className="w-32 h-32 opacity-20 hover:opacity-60" />
      </div>

      {/* Centered login form */}
      <div className="flex items-center justify-center">
        <form
          onSubmit={handleLogin}
          className="bg-white p-8 rounded shadow-md w-full max-w-lg"
        >
          <h2 className="text-2xl text-black font-bold mb-6 text-center">Login</h2>

          <div className="mb-4">
            <label className="block text-gray-600 text-sm mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="text-black w-full border px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your e-mail"
            />
          </div>

          <div className="mb-6">
            <label className="block text-gray-600 text-sm mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="text-black w-full border px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your password"
            />
          </div>
          <div className="grid grid-cols-2 gap-4 mt-4">
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition"
            >
              Login
            </button>

            <button
              type="button"
              onClick={() => navigate('/register')}
              className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 transition"
            >
              Register
            </button>
          </div>
        </form>
      </div>

      {/* Right gear */}
      <div className="flex items-end justify-end px-2">
        <img src="/gears.svg" alt="Gear Right" className="w-32 h-32 opacity-20 hover:opacity-60" />
      </div>
    </div>
  )
}

