import { Link } from 'react-router-dom';

function CollectionList() {
  // Тимчасово використовуємо статичний список, поки не додамо ендпоінт для списку колекцій
  const collections = [{ id: 16, name: 'Updated Project Folder' }];

  return (
    <div>
      <h2>Collections</h2>
      <ul className="list-group">
        {collections.map((collection) => (
          <li key={collection.id} className="list-group-item">
            <Link to={`/collections/${collection.id}`}>{collection.name}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default CollectionList;