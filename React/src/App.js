import React from 'react';
import { Route } from 'react-router-dom';
import 'antd/dist/antd.css'
import './App.css';
// import NavigationPage from './components/index'
import UrlAnalysis from './components/urlAnalysis'

const App = () => (
    <div className="app">
        <main>
            <Route exact path="/" component={ UrlAnalysis }/>
        </main>
    </div>

)


export default App;
