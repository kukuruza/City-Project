```
collection=5f08583b1f45a9a7c7193c87bbfa9088

python src/augmentation/collections/FinalizeCollection.py \
  --collection_id ${collection}

python src/augmentation/collections/RenderCollectionExamples.py \
  --collection_id ${collection}

python src/augmentation/collections/ManuallyFilterCollection.py \
  --collection_id ${collection} \
  --task problem

python src/augmentation/collections/ManuallyFilterCollection.py \
  --collection_id ${collection} \
  --task type

python src/augmentation/collections/ManuallyFilterCollection.py \
  --collection_id ${collection} \
  --task color

```