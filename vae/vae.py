"""VAE contains the variational auto-encoder convenience class."""
import tensorflow as tf

from vae.decoder import decoder
from vae.encoder import encoder
from vae.prior import prior


class VAE:
    """VAE is a wrapper around a ful variational auto-encoder graph.

    Attributes:
        input (tf.Tensor): Points to image input placeholder.
        latent (tf.Tensor): Points to latent variable sample tensor.
        loss (tf.Tensor): Points to the ELBO loss tensor.
        prior (tf.distribution.Normal): Prior distribution.
        encoder (tf.distribution.Normal): Encoder / recognition distribution.
        decoder (tf.distribution.Normal): Decoder distribution.
    """

    def __init__(self, img_size, batch_size=20, latent_size=10,
                 sample_size=1, units=500):
        """Creates a new instance of VAE.

        This creates the complete static graph, which is accessed afterwards
        only through session runs.

        Args:
            img_size (int): Flattened dim of input image.
            batch_size (int): The minibatch size, determines input tensor dims.
            latent_size (int): Dimension of the latent normal variable.
            sample_size (int): The sample size drawn from the recognition model.
                Usually 1, since we do stochastic integration.
        """
        self.input = tf.placeholder(tf.float32, [batch_size, img_size])
        # batch_size, img_size
        self.encoder = encoder(self.input, latent_size, units)
        # batch_shape is (batch_size, latent_size)
        self.latent = self.encoder.sample(sample_size)
        # sample_size, batch_size, latent_size
        self.decoder = decoder(self.latent, img_size, units)
        # batch_shape is (sample_size, batch_size, latent_size)
        self.prior = prior(sample_size, batch_size, latent_size)
        # batch_shape is (sample_size, batch_size, latent_size)

        likelihood = self.decoder.log_prob(self.input)
        # get likelihood over each sample
        # reduce_sum entire tensor, divide by sample_size
        latent_prior = self.prior.log_prob(self.latent)
        # get prior over each sample
        # reduce_sum entire tensor, divide by sample_size
        latent_posterior = self.encoder.log_prob(self.latent)
        # get posterior per sample
        # reduce_sum entire tensor, divide by sample size

        self.loss = (
            tf.reduce_sum(likelihood) / sample_size +
            tf.reduce_sum(latent_prior) / sample_size -
            tf.reduce_sum(latent_posterior) / sample_size
        )
        # scalar

    def decode(self, latent):
        """Decodes the provided latent array, returns a sample from the output.

        Args:
            latent (np.ndarray): A sample_size x batch_size x latent_size
                latent variable array.

        Returns:
            np.ndarray: A sample_size x batch_size, img_size array of sampled
                and decoded images.
        """
        sess = tf.Session()
        img = sess.run(self.decoder.sample(), data_dict={self.latent: latent})
        return img

    def encode(self, img):
        """Encodes the provided images, returns a sample from the latent posterior.

        Args:
            img (np.ndarray): A batch_size x img_size array of flattened images.

        Returns:
            np.ndarray: A sample_size x batch_size x latent_size ndarray of
                latent variables.
        """
        sess = tf.Session()
        latent = sess.run(self.latent, data_dict={self.input: img})
        return latent
