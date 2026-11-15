import { useState } from 'react'
import reactLogo from './assets/react.svg'
import './App.css'
import {BrowserRouter as Router,Routes,Route} from 'react-router-dom'
import LoginPage from './assets/LoginPage.jsx'
import RegisterPage from './assets/RegisterPage.jsx';
import ChatPage from './assets/ChatPage.jsx';
function App() {
  const [count, setCount] = useState(0)

  return (
   <Router>
    <Routes>
      <Route path='/' element={<LoginPage/>}/>
      <Route path='/register' element={<RegisterPage/>}/>
      <Route path='/chat' element={<ChatPage/>}/>
    </Routes>
   </Router>
  )
}

export default App;
