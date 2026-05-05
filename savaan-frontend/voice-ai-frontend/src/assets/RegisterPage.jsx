import { useState } from "react";
import API from "../utils/api";
import { useNavigate } from "react-router-dom";

export default function RegisterPage() {

    const navigate = useNavigate();
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('');

    const handleRegistration = async (e) => {
        e.preventDefault();
        console.log("Attempting to register:", email);

        try {
            const response = await API.post('/register', {
                email,
                password,
            });

            if (response.status == 201) {
                alert("Registration succesful, Login to proceed");
                navigate("/")
            } else if (response.status == 409) {
                alert("You are already a registered user, Login to proceed");
                navigate("/")
            }
            else {
                alert("Registration failed, please retry");
            }
        } catch (e) {
            console.log("Registration failed due to", e);

            if (e.response && e.response.status === 409) {
                alert("You are already a registered user, Login to proceed");
                navigate("/");
            } else {
                alert("Registration failed, please retry.");
            }
        }
    }

    return (
        <div className="grid grid-cols-3 min-h-screen bg-black-100 relative">
            {/* Left gear */}
            <div className="flex items-start justify-start px-4">
                <img src="/gears.svg" alt="Gear Left" className="w-32 h-32 opacity-20 hover:opacity-60" />
            </div>

            {/* Centered login form */}
            <div className="flex items-center justify-center">
                <form
                    onSubmit={handleRegistration}
                    className="bg-white p-8 rounded shadow-md w-full max-w-lg"
                >
                    <h2 className="text-2xl text-black font-bold mb-6 text-center">Register</h2>
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
                    <button
                        type="submit"
                        className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700 transition"
                    >
                        Register
                    </button>
                </form>
            </div>

            {/* Right gear */}
            <div className="flex items-end justify-end px-2">
                <img src="/gears.svg" alt="Gear Right" className="w-32 h-32 opacity-20 hover:opacity-60" />
            </div>
        </div>
    )
}