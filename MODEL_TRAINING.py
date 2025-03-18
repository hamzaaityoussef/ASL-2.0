import os
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical, Sequence
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Flatten, Dropout
from tensorflow.keras.optimizers import Adam

class DataGenerator(Sequence):
    def __init__(self, image_paths, labels, batch_size=32, dim=(300, 300), n_channels=3, n_classes=None, shuffle=True):
        self.image_paths = image_paths
        self.labels = labels
        self.batch_size = batch_size
        self.dim = dim
        self.n_channels = n_channels
        self.n_classes = n_classes
        self.shuffle = shuffle
        self.indexes = np.arange(len(self.image_paths))
        if self.shuffle:
            np.random.shuffle(self.indexes)

    def __len__(self):
        return int(np.ceil(len(self.image_paths) / self.batch_size))

    def __getitem__(self, index):
        indexes = self.indexes[index * self.batch_size:(index + 1) * self.batch_size]
        batch_paths = [self.image_paths[k] for k in indexes]
        X, y = self.__data_generation(batch_paths, indexes)
        return X, y

    def on_epoch_end(self):
        if self.shuffle:
            np.random.shuffle(self.indexes)

    def __data_generation(self, batch_paths, indexes):
        X = np.empty((len(batch_paths), *self.dim, self.n_channels))
        y = np.empty((len(batch_paths)), dtype=int)

        for i, (path, idx) in enumerate(zip(batch_paths, indexes)):
            img = cv2.imread(path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            X[i,] = img / 255.0
            y[i] = self.labels[idx]

        return X, to_categorical(y, num_classes=self.n_classes)

def prepare_data():
    data_dir = "Data"
    categories = os.listdir(data_dir)
    
    image_paths = []
    labels = []
    
    for idx, category in enumerate(categories):
        path = os.path.join(data_dir, category)
        for img_name in os.listdir(path):
            img_path = os.path.join(path, img_name)
            image_paths.append(img_path)
            labels.append(idx)
    
    return image_paths, labels, categories

def create_model(num_classes):
    model = Sequential([
        # First Convolutional Block
        Conv2D(32, (3, 3), activation='relu', input_shape=(300, 300, 3)),
        MaxPooling2D((2, 2)),
        
        # Second Convolutional Block
        Conv2D(64, (3, 3), activation='relu'),
        MaxPooling2D((2, 2)),
        
        # Third Convolutional Block
        Conv2D(128, (3, 3), activation='relu'),
        MaxPooling2D((2, 2)),
        
        # Fourth Convolutional Block
        Conv2D(128, (3, 3), activation='relu'),
        MaxPooling2D((2, 2)),
        
        # Flatten and Dense Layers
        Flatten(),
        Dense(512, activation='relu'),
        Dropout(0.5),
        Dense(num_classes, activation='softmax')
    ])
    
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

def main():
    # Prepare data paths and labels
    print("Preparing data...")
    image_paths, labels, categories = prepare_data()
    num_classes = len(categories)
    
    # Split data
    paths_train, paths_test, labels_train, labels_test = train_test_split(
        image_paths, labels, test_size=0.2, random_state=42
    )
    
    # Create data generators
    train_generator = DataGenerator(
        paths_train, 
        labels_train,
        batch_size=32,
        n_classes=num_classes
    )
    
    test_generator = DataGenerator(
        paths_test,
        labels_test,
        batch_size=32,
        n_classes=num_classes,
        shuffle=False
    )
    
    # Create and compile model
    print("Creating model...")
    model = create_model(num_classes)
    model.summary()
    
    # Train the model
    print("Training model...")
    history = model.fit(
        train_generator,
        epochs=2,
        validation_data=test_generator
    )
    
    # Evaluate the model
    print("Evaluating model...")
    test_loss, test_accuracy = model.evaluate(test_generator)
    print(f"Test accuracy: {test_accuracy*100:.2f}%")
    
    # Save the model
    print("Saving model...")
    model.save('sign_language_model.h5')
    
    # Save the categories
    with open('categories.txt', 'w') as f:
        for category in categories:
            f.write(f"{category}\n")

if __name__ == "__main__":
    main()
