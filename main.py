"""Main File
"""

# Python standard imports
from argparse import ArgumentParser

# Pytorch and lightning imports
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping
from pytorch_lightning.loggers import WandbLogger

# Model
from project.few_shot import FewShot

# Datamodule
from project.dataloader import FewShotDataModule

parser = ArgumentParser()

if __name__=='__main__':
    parser = FewShotDataModule.add_model_specific_args(parser)
    parser = FewShot.add_model_specific_args(parser)
    args = parser.parse_args()

    # Neptune credentials. User-specific. You need to create you Neptune accout!
    wandb_logger = WandbLogger(project='few-shot-learning-clip', job_type='train')

    # Model instance
    few_model = FewShot(learning_rate=args.learning_rate)

    # Datamodule
    dm = FewShotDataModule(ops=few_model.preprocess)
    dm.prepare_data()

    # Training step
    dm.setup(stage='fit')

    # Callbacks to early stop and save the best models
    stop_cb = EarlyStopping(monitor='valid_global_acc', mode='max', patience=5, verbose=True)
    chkpoint_cb = ModelCheckpoint(monitor='valid_global_acc', dirpath='./checkpoints/',
                                    filename='fewshot-{epoch:02d}-{acc:.2f}',
                                    mode='max')

    trainer = pl.Trainer(gpus=1, precision=16, logger=wandb_logger, callbacks=[chkpoint_cb, stop_cb],
                         max_epochs=args.max_epochs)
    trainer.fit(few_model, dm)

    # Test stage -> loading the best model according to validation accuracy
    dm.setup(stage='test')
    few_model = FewShot.load_from_checkpoint(trainer.checkpoint_callback.best_model_path)
    trainer.test(few_model, datamodule=dm)
