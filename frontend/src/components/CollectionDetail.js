import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getCollection, updateCollection, uploadPhoto, deletePhoto } from '../api';

function CollectionDetail() {
  const { id } = useParams();
  const [collection, setCollection] = useState(null);
  const [name, setName] = useState('');
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCollection = async () => {
      try {
        const data = await getCollection(id);
        setCollection(data);
        setName(data.name);
      } catch (err) {
        setError('Failed to load collection');
      }
    };
    fetchCollection();
  }, [id]);

  const handleNameUpdate = async (e) => {
    e.preventDefault();
    try {
      const updatedCollection = await updateCollection(id, name);
      setCollection(updatedCollection);
      setError(null);
    } catch (err) {
      setError('Failed to update collection name');
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handlePhotoUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    try {
      const uploadedPhotos = await uploadPhoto(id, file);
      setCollection((prev) => ({
        ...prev,
        photos: [...prev.photos, ...uploadedPhotos],
      }));
      setFile(null);
      setError(null);
    } catch (err) {
      setError('Failed to upload photo');
    }
  };

  const handlePhotoDelete = async (photoId) => {
    try {
      await deletePhoto(id, photoId);
      setCollection((prev) => ({
        ...prev,
        photos: prev.photos.filter((photo) => photo.id !== photoId),
      }));
      setError(null);
    } catch (err) {
      setError('Failed to delete photo');
    }
  };

  if (!collection) return <div>Loading...</div>;

  return (
    <div>
      <h2>{collection.name}</h2>
      {error && <div className="alert alert-danger">{error}</div>}
      
      <h3>Edit Collection Name</h3>
      <form onSubmit={handleNameUpdate} className="mb-4">
        <div className="input-group">
          <input
            type="text"
            className="form-control"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">Update Name</button>
        </div>
      </form>

      <h3>Upload Photo</h3>
      <form onSubmit={handlePhotoUpload} className="mb-4">
        <div className="input-group">
          <input
            type="file"
            className="form-control"
            onChange={handleFileChange}
            accept="image/*"
          />
          <button type="submit" className="btn btn-primary" disabled={!file}>
            Upload
          </button>
        </div>
      </form>

      <h3>Photos</h3>
      <div className="row">
        {collection.photos.map((photo) => (
          <div key={photo.id} className="col-md-4 mb-3">
            <div className="card">
              <img
                src={`http://localhost:8000${photo.file}`}
                className="card-img-top"
                alt="Photo"
              />
              <div className="card-body">
                <button
                  className="btn btn-danger"
                  onClick={() => handlePhotoDelete(photo.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default CollectionDetail;