"""Check mathematical invariants and independent reference solutions."""

import numpy as np
import pytest
import pywt
from signal_inverse import optimization as opt, wavelets, time_frequency as tf, separation
from signal_inverse.metrics import psnr, si_sdr


@pytest.mark.parametrize("shape", [(7,9),(1,8),(8,1),(1,1)])
def test_discrete_gradient_adjoint(shape):
    rng=np.random.default_rng(7)
    x=rng.normal(size=shape)
    field=rng.normal(size=(*shape,2))
    assert np.allclose(np.sum(opt.gradient(x)*field),np.sum(x*opt.gradient_adjoint(field)),atol=1e-12)


def test_denoising_gradient_by_directional_difference():
    rng=np.random.default_rng(2)
    x,y,direction=rng.normal(size=(3,6,8))
    weight=0.8
    epsilon=1e-6
    derivative=(opt.denoising_cost(x+epsilon*direction,y,weight)-opt.denoising_cost(x-epsilon*direction,y,weight))/(2*epsilon)
    analytic=np.sum(direction*(x-y+weight*opt.gradient_adjoint(opt.gradient(x))))
    assert np.isclose(derivative,analytic,rtol=1e-7,atol=1e-7)


def test_denoising_against_dense_linear_system():
    rng=np.random.default_rng(3)
    y=rng.normal(size=(4,5))
    n=y.size
    basis=np.eye(n).reshape(n,*y.shape)
    laplacian=np.column_stack([opt.gradient_adjoint(opt.gradient(e)).ravel() for e in basis])
    weight=0.2
    expected=np.linalg.solve(np.eye(n)+weight*laplacian,y.ravel()).reshape(y.shape)
    result=opt.denoise(y,weight,iterations=250)
    assert np.allclose(result.image,expected,atol=1e-10)
    assert np.all(np.diff(result.costs)<=1e-10)


def test_inpainting_against_constrained_linear_system():
    rng=np.random.default_rng(6)
    shape=(4,5)
    image=rng.normal(size=shape)
    mask=np.zeros(shape,dtype=bool)
    mask[0,:]=True
    mask[-1,-1]=True
    observation=image*mask
    n=image.size
    laplacian=np.column_stack([opt.gradient_adjoint(opt.gradient(e.reshape(shape))).ravel() for e in np.eye(n)])
    known=mask.ravel()
    expected=observation.ravel().copy()
    expected[~known]=np.linalg.solve(laplacian[np.ix_(~known,~known)],-laplacian[np.ix_(~known,known)]@expected[known])
    result=opt.inpaint(observation,mask,iterations=1500)
    assert np.array_equal(result.image[mask],observation[mask])
    assert np.allclose(result.image.ravel(),expected,atol=1e-8)
    assert np.all(np.diff(result.costs)<=1e-10)


def test_quadratic_convergence_boundary():
    trajectory,_=opt.quadratic_descent(0.25,iterations=40)
    assert np.isclose(abs(trajectory[-1,1]),0.6)
    stable,_=opt.quadratic_descent(0.2,iterations=100)
    assert np.linalg.norm(stable[-1])<1e-8


@pytest.mark.parametrize("transform",["dwt","swt"])
def test_zero_threshold_reconstruction(transform):
    image=np.random.default_rng(4).normal(size=(64,64))
    recovered=wavelets.denoise(image,threshold=0,level=2,wavelet="haar",transform=transform)
    assert np.allclose(image,recovered,atol=1e-12)


def test_threshold_does_not_erase_approximation():
    image=np.random.default_rng(1).normal(size=(64,64))
    actual=wavelets.denoise(image,threshold=1e6,level=2,wavelet="haar")
    expected=wavelets.remove_orientation(image,"all",wavelet="haar",level=2)
    assert np.allclose(actual,expected)


def test_wavelet_components_sum_to_signal():
    x=np.random.default_rng(8).normal(size=1024)
    components=[wavelets.reconstruct_component(x,level=5)]
    components += [wavelets.reconstruct_component(x,level=5,detail_level=j) for j in range(1,6)]
    assert np.allclose(np.sum(components,axis=0),x,atol=1e-10)


@pytest.mark.parametrize("width,overlap",[(128,32),(512,448)])
def test_stft_roundtrip(width,overlap):
    x=np.random.default_rng(1).normal(size=(2,2345))
    _,_,coeff=tf.stft(x,15000,width,overlap)
    restored=tf.inverse_stft(coeff,15000,x.shape[-1],width,overlap)
    assert restored.shape==x.shape
    assert np.allclose(restored,x,atol=1e-12)


def test_real_l1_has_primal_dual_optimality_certificate():
    rng=np.random.default_rng(1)
    matrix=separation.mixing_matrix([0.17,0.88,1.61,2.81])
    points=rng.normal(size=(12,2))
    solution=separation.minimum_l1_real(points,matrix)
    assert np.allclose(solution@matrix.T,points,atol=1e-12)
    for point,estimate in zip(points,solution):
        # A feasible dual p with A^T p in [-1,1] gives a lower bound p^T x.
        # Equality with the feasible primal cost proves global optimality.
        active=np.flatnonzero(abs(estimate)>1e-10)
        dual=np.linalg.solve(matrix[:,active].T,np.sign(estimate[active]))
        assert np.max(abs(matrix.T@dual)) <= 1+1e-10
        assert np.isclose(np.sum(abs(estimate)),dual@point,atol=1e-10)


def test_split_l1_preserves_unmasked_mixtures():
    rng=np.random.default_rng(9)
    matrix=separation.mixing_matrix([np.pi/6,np.pi/2,5*np.pi/6])
    coeff=rng.normal(size=(2,8,5))+1j*rng.normal(size=(2,8,5))
    result=separation.split_l1(coeff,matrix,discard_percentile=0)
    assert np.allclose(np.einsum('ij,jft->ift',matrix,result),coeff,atol=1e-12)


def test_si_sdr_scale_invariance_and_permutation():
    rng=np.random.default_rng(5)
    reference=rng.normal(size=(3,1024))
    estimate=reference+0.1*rng.normal(size=reference.shape)
    assert np.isclose(si_sdr(reference[0],estimate[0]),si_sdr(reference[0],-3*estimate[0]))
    aligned,scores=separation.match_sources(reference,estimate[[2,0,1]])
    assert np.array_equal(aligned,estimate)
    assert all(score>15 for score in scores)


def test_psnr_uses_fixed_range():
    assert psnr(np.ones((3,3)),0.9*np.ones((3,3)))==pytest.approx(20)
    assert psnr(np.zeros((3,3)),np.zeros((3,3)))==float('inf')
