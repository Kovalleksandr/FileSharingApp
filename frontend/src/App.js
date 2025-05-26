import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import CollectionList from './components/CollectionList';
import CollectionDetail from './components/CollectionDetail';

function App() {
  return (
    <Router>
      <div className="container">
        <h1>File Sharing App</h1>
        <Routes>
          <Route path="/" element={<CollectionList />} />
          <Route path="/collections/:id" element={<CollectionDetail />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;